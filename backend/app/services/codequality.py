from huggingface_hub import login, hf_hub_download, snapshot_download
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import subprocess
import torch
from llama_cpp import Llama

load_dotenv()

hugging_face_token = os.getenv('hugging_face_token')
login(token=hugging_face_token)

# ── Configuration ────────────────────────────────────────────────────────────
REPO_ID       = "sujalgawas/my-codellama-experience-model"
BASE_MODEL_ID = "codellama/CodeLlama-7b-hf"
PTH_FILENAME  = "Codellama_v2.pth"
GGUF_FILENAME = "codellama.gguf"
GGUF_Q4_NAME  = "codellama-q4.gguf"
LORA_SCALE    = 1.0
QUANT_TYPE    = "q4_k_m"

# ── Derived paths ────────────────────────────────────────────────────────────
cache_dir    = Path("./cache")
llama_dir    = cache_dir / "llama.cpp"
model_dir    = Path("./app/utils")
hf_model_dir = model_dir / "codellama_hf"
pth_path     = model_dir / PTH_FILENAME

hf_model_dir.mkdir(parents=True, exist_ok=True)

model_gguf    = model_dir / GGUF_FILENAME
model_gguf_q4 = model_dir / GGUF_Q4_NAME

if model_gguf_q4.exists():
    print("model exists")
else:
    # Download your fine-tuned .pth 
    if not pth_path.exists():
        print("Downloading fine-tuned .pth weights...")
        hf_hub_download(
            repo_id=REPO_ID,
            filename=PTH_FILENAME,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False,
        )

    #Download ONLY config + tokenizer files (no weights, ~10MB)
    config_json = hf_model_dir / "config.json"
    if not config_json.exists():
        print("Downloading config and tokenizer files only (no model weights)...")
        snapshot_download(
            repo_id=BASE_MODEL_ID,
            local_dir=str(hf_model_dir),
            local_dir_use_symlinks=False,
            token=hugging_face_token,
            # Skip all weight files — we only want config + tokenizer
            ignore_patterns=[
                "*.bin", "*.bin.index.json",
                "*.safetensors", "*.safetensors.index.json",
                "*.pt", "*.pth",
                "original/*",
            ],
        )
        print("  Config and tokenizer downloaded.")
        
    # Merge LoRA adapters into full-precision base weights
    weights_dest = hf_model_dir / "pytorch_model.bin"
    cleaned_flag = hf_model_dir / ".keys_cleaned_v5"

    # Delete any partial GGUF from a previous failed conversion
    if model_gguf.exists() and not model_gguf_q4.exists():
        model_gguf.unlink()
        print("  Deleted partial codellama.gguf from failed conversion")

    if not cleaned_flag.exists():
        # Clean up old merge artifacts
        for old_flag in hf_model_dir.glob(".keys_cleaned*"):
            old_flag.unlink()
            print(f"  Removed old sentinel: {old_flag.name}")
        if weights_dest.exists():
            weights_dest.unlink()
            print("  Deleted old pytorch_model.bin")

        # Ensure full-precision base model weights are available
        has_base_weights = (
            any(hf_model_dir.glob("model*.safetensors"))
            or any(hf_model_dir.glob("pytorch_model-*.bin"))
        )
        if not has_base_weights:
            print("Downloading full base model weights (one-time, ~13 GB)...")
            snapshot_download(
                repo_id=BASE_MODEL_ID,
                local_dir=str(hf_model_dir),
                local_dir_use_symlinks=False,
                token=hugging_face_token,
                ignore_patterns=["original/*"],
            )

        # Install transformers if needed (for loading sharded weights correctly)
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', 'transformers'],
            check=True,
        )
        from transformers import AutoModelForCausalLM
        import gc

        # Load full-precision base model
        print("Loading full-precision base model...")
        base_model = AutoModelForCausalLM.from_pretrained(
            str(hf_model_dir),
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        )
        base_sd = {k: v.clone() for k, v in base_model.state_dict().items()}
        del base_model; gc.collect()
        print(f"  Base model: {len(base_sd)} tensors")

        # Extract LoRA adapters from .pth
        print("Extracting LoRA adapters from .pth...")
        pth = torch.load(str(pth_path), map_location="cpu")
        for wk in ("model_state_dict", "state_dict", "model"):
            if isinstance(pth, dict) and wk in pth:
                pth = pth[wk]
                break

        lora_A, lora_B = {}, {}
        for k, v in pth.items():
            k = k.replace("base_model.model.", "", 1)
            if ".lora_A.default.weight" in k:
                lora_A[k.replace(".lora_A.default.weight", "")] = v.float()
            elif ".lora_B.default.weight" in k:
                lora_B[k.replace(".lora_B.default.weight", "")] = v.float()
            elif ".lora_A.weight" in k:
                lora_A[k.replace(".lora_A.weight", "")] = v.float()
            elif ".lora_B.weight" in k:
                lora_B[k.replace(".lora_B.weight", "")] = v.float()
        del pth; gc.collect()
        print(f"  LoRA modules: {len(lora_A)} A, {len(lora_B)} B")

        # Merge LoRA into base weights
        for prefix in sorted(lora_A):
            if prefix not in lora_B:
                print(f"  SKIP (no B): {prefix}"); continue
            wkey = prefix + ".weight"
            if wkey not in base_sd:
                print(f"  SKIP (not in base): {wkey}"); continue

            W = base_sd[wkey].float()
            A, B = lora_A[prefix], lora_B[prefix]
            rank = A.shape[0]
            delta = B @ A

            if delta.shape == W.shape:
                base_sd[wkey] = (W + delta * (LORA_SCALE / rank)).half()
                print(f"  Merged: {wkey}  rank={rank}")
            elif delta.T.shape == W.shape:
                base_sd[wkey] = (W + delta.T * (LORA_SCALE / rank)).half()
                print(f"  Merged (T): {wkey}  rank={rank}")
            else:
                print(f"  MISMATCH: {wkey} W={W.shape} delta={delta.shape}")

        del lora_A, lora_B; gc.collect()

        # Save merged weights as single pytorch_model.bin
        print(f"Saving merged weights ({len(base_sd)} tensors)...")
        torch.save(base_sd, str(weights_dest))
        del base_sd; gc.collect()

        # Remove original base weight files so converter uses our merged bin
        for pat in ("*.safetensors", "*.safetensors.index.json",
                    "model.safetensors.index.json",
                    "pytorch_model.bin.index.json", "pytorch_model-*.bin"):
            for f in hf_model_dir.glob(pat):
                f.unlink()
                print(f"  Removed: {f.name}")

        cleaned_flag.touch()
        print(f"  Saved to {weights_dest}")
        
    # git clone llama.cpp 
    if not llama_dir.exists():
        print("Cloning llama.cpp...")
        subprocess.run(['git', 'clone', 'https://github.com/ggerganov/llama.cpp',
                        str(llama_dir)], check=True)

    #Install llama.cpp requirements
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r',
                    str(llama_dir / 'requirements.txt')], check=True)

    #Convert HF folder → GGUF
    if not model_gguf.exists():
        print("Converting to GGUF...")
        subprocess.run([
            sys.executable, str(llama_dir / 'convert_hf_to_gguf.py'),
            str(hf_model_dir),
            '--outfile', str(model_gguf),
            '--outtype', 'f16',
        ], check=True)

    # Build llama.cpp quantize binary (cross-platform via cmake)
    build_dir = llama_dir / 'build'
    if sys.platform == 'win32':
        quantize_exe = build_dir / 'bin' / 'Release' / 'llama-quantize.exe'
    else:
        quantize_exe = build_dir / 'bin' / 'llama-quantize'

    if not quantize_exe.exists():
        print("Building llama.cpp quantize tool...")
        # Ensure cmake is available
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', 'cmake'],
            check=True,
        )
        build_dir.mkdir(exist_ok=True)
        subprocess.run(['cmake', '..'], cwd=str(build_dir), check=True)
        subprocess.run(
            ['cmake', '--build', '.', '--config', 'Release'],
            cwd=str(build_dir), check=True,
        )

    #Quantize to Q4_K_M
    if not model_gguf_q4.exists():
        print("Quantizing to Q4_K_M...")
        subprocess.run([str(quantize_exe), str(model_gguf), str(model_gguf_q4), QUANT_TYPE], check=True)

text = """
import random

numbers = [random.randint(1, 100) for _ in range(10)]
total = 0

for n in numbers:
    if n % 2 == 0:
        total += n
    else:
        total += 1

average = total / len(numbers)

print("Numbers:", numbers)
print("Total:", total)
print("Average:", average)
print("Done")
"""

from transformers import AutoTokenizer
from torch import nn

#load_model
def load_llama():
    model = Llama(model_path = "./app/utils/codellama.gguf",
                  chat_format='llama',
                  embedding = True,
                  n_ctx=512,
                  n_threads=8
                  )
    return model

#classifer model
class CodeClassifier(nn.Module):

    def __init__(self, input_size=4096):
        super().__init__()

        self.classifier = nn.Linear(input_size, 1)

    def forward(self, x):

        return torch.sigmoid(self.classifier(x))
    
#embedding
def get_embedding(llm, text):

    embedding = llm.create_embedding(text)

    vector = embedding["data"][0]["embedding"]

    tensor_vec = torch.tensor(vector)
    
    if tensor_vec.dim() == 2:
        tensor_vec = tensor_vec.mean(dim=0)
        
    return tensor_vec.unsqueeze(0)

#load_classifier
def load_classifier():

    model = CodeClassifier()

    state_dict = torch.load('./app/utils/Codellama_v2.pth', map_location="cpu")

    if "state_dict" in state_dict:
        state_dict = state_dict["state_dict"]

    model.load_state_dict(state_dict, strict=False)

    model.eval()

    return model

#inferencing
def predict(llm, classifier, text):

    print("Creating embedding...")

    embedding = get_embedding(llm, text)

    with torch.no_grad():

        score = classifier(embedding)

    print(f"\nPrediction Score: {score.item():.4f}")
    
    if score.item() > 0.5:
        print("Prediction: Senior")
    else:
        print("Prediction: Intern")

llm = load_llama()

classifier = load_classifier()

predict(llm, classifier, text)
