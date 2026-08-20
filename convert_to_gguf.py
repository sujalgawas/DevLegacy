"""
convert_to_gguf.py
==================
this script is created to generate 4 bit quantized version of the model

Steps performed automatically:
  1. Download base model from Hugging Face (cached locally).
  2. Download LoRA adapter from Hugging Face (cached locally).
  3. Merge adapter into base model → saves full HF checkpoint.
  4. Clone llama.cpp (or reuse existing clone) for the conversion tools.
  5. Install llama.cpp Python conversion requirements.
  6. Convert merged HF model → GGUF (fp16 intermediate).
  7. Quantize GGUF to Q4_K_M (~1 GB for 1.5B model → fits in ~1.2 GB RAM).
  8. Place the final .gguf file in OUTPUT_GGUF_PATH.
"""

BASE_MODEL_REPO    = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
ADAPTER_MODEL_REPO = "sujalgawas/qwen2.5-coder-1.5b-code-reviewer"

QUANT_TYPE = "Q4_K_M"

from pathlib import Path
import os
import subprocess
import sys

SCRIPT_DIR     = Path(__file__).parent.resolve()
WORK_DIR       = SCRIPT_DIR / "gguf_workspace"
BASE_DIR       = WORK_DIR / "base"
ADAPTER_DIR    = WORK_DIR / "adapter"
MERGED_HF_DIR  = WORK_DIR / "merged_hf"
LLAMA_CPP_DIR  = WORK_DIR / "llama.cpp"
GGUF_FP16_PATH = WORK_DIR / "model_fp16.gguf"

OUTPUT_GGUF_PATH = SCRIPT_DIR / "backend" / "app" / ".cache" / "models" / "model_q4km.gguf"



def run(cmd: list, cwd=None):
    """Run a shell command, stream output, raise on failure."""
    print(f"\n  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def pip_install(*packages: str):
    run([
        sys.executable, "-m", "pip", "install",
        "--quiet",
        "--ignore-installed",
        *packages,
    ])


#  dependencies 

print("STEP 0 — Installing / verifying Python dependencies")

pip_install(
    "torch",
    "transformers",
    "peft",
    "huggingface_hub",
    "sentencepiece",
    "gguf",
    "numpy",
)

from huggingface_hub import login, snapshot_download  
from huggingface_hub.errors import HfHubHTTPError

from transformers import AutoTokenizer, AutoModelForCausalLM  
from peft import PeftModel  
import torch  


hf_token = os.environ.get("HUGGING_FACE_TOKEN") or os.environ.get("HF_TOKEN")
if hf_token:
    try:
        login(token=hf_token)

    except HfHubHTTPError as e:
        print(f"Hugging Face authentication/API error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")

WORK_DIR.mkdir(parents=True, exist_ok=True)

print(f"Downloading base model: {BASE_MODEL_REPO}")

if BASE_DIR.exists() and any(BASE_DIR.iterdir()):
    print(f"Already cached at {BASE_DIR}")
else:
    print("model not found in disk")
    snapshot_download(repo_id=BASE_MODEL_REPO, local_dir=str(BASE_DIR))
    print(f"downloaded model to {BASE_DIR}")


print(f"Downloading LoRA adapter: {ADAPTER_MODEL_REPO}")

if ADAPTER_DIR.exists() and any(ADAPTER_DIR.iterdir()):
    print(f"Already cached at {ADAPTER_DIR}")
else:
    snapshot_download(repo_id=ADAPTER_MODEL_REPO, local_dir=str(ADAPTER_DIR))
    print(f"downloaded model to {ADAPTER_DIR}")


print("Merging base + LoRA adapter")

if MERGED_HF_DIR.exists() and any(MERGED_HF_DIR.iterdir()):
    print(f"Already merged at {MERGED_HF_DIR}")
else:
    tokenizer = AutoTokenizer.from_pretrained(str(BASE_DIR))

    base_model = AutoModelForCausalLM.from_pretrained(
        str(BASE_DIR),
        torch_dtype=torch.float16,  # float16 for CPU
        low_cpu_mem_usage=True,
        device_map="cpu",
    )

    peft_model = PeftModel.from_pretrained(
        base_model,
        str(ADAPTER_DIR),
        is_trainable=False,
    )

    merged = peft_model.merge_and_unload()
    merged.eval()

    MERGED_HF_DIR.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(MERGED_HF_DIR), safe_serialization=True)
    tokenizer.save_pretrained(str(MERGED_HF_DIR))

    del merged, peft_model, base_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    import gc; gc.collect()



print("Setting up llama.cpp conversion tools")

if LLAMA_CPP_DIR.exists():
    print("  Updating existing llama.cpp clone …")
    run(["git", "pull"], cwd=LLAMA_CPP_DIR)
else:
    print("  Cloning llama.cpp …")
    run([
        "git", "clone", "--depth=1",
        "https://github.com/ggerganov/llama.cpp",
        str(LLAMA_CPP_DIR),
    ])



print("Converting merged HF model → fp16 GGUF")

# llama.cpp renamed the script over time; handle both
convert_script = LLAMA_CPP_DIR / "convert_hf_to_gguf.py"
if not convert_script.exists():
    convert_script = LLAMA_CPP_DIR / "convert.py"

if not convert_script.exists():
    print("ERROR: Could not find convert_hf_to_gguf.py or convert.py in llama.cpp.")
    sys.exit(1)

if GGUF_FP16_PATH.exists():
    print(f"fp16 GGUF already exists at {GGUF_FP16_PATH}, skipping")
else:
    run([
        sys.executable, str(convert_script),
        str(MERGED_HF_DIR),
        "--outfile", str(GGUF_FP16_PATH),
        "--outtype", "f16",
    ])
    print(f"fp16 GGUF saved to {GGUF_FP16_PATH}")


print(f"Quantizing to {QUANT_TYPE}")

import platform
import urllib.request
import zipfile
import tarfile
import json as _json

OUTPUT_GGUF_PATH.parent.mkdir(parents=True, exist_ok=True)
PREBUILT_DIR = WORK_DIR / "llama_prebuilt"

IS_WINDOWS = platform.system() == "Windows"

QUANTIZE_NAME = "llama-quantize.exe"

def _find_quantize_in_dir(directory: Path):
    """Recursively search for llama-quantize binary under directory."""
    for candidate in directory.rglob(QUANTIZE_NAME):
        if candidate.is_file():
            return candidate
    return None


def _download_prebuilt_quantize() -> Path:
    """Download the latest pre-built llama.cpp release — no compiler needed."""
    print("  Fetching latest llama.cpp release info from GitHub ...")
    api_url = "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
    req = urllib.request.Request(api_url, headers={"User-Agent": "convert_to_gguf"})
    with urllib.request.urlopen(req) as resp:
        release = _json.loads(resp.read().decode())

    tag    = release["tag_name"]
    assets = release["assets"]
    print(f"Latest release: {tag}")

    
    priorities = [
        "-bin-win-avx2-x64.zip",
        "-bin-win-avx-x64.zip",
        "-bin-win-noavx-x64.zip",
        "-bin-win-cuda-12.4-x64.zip",
        "-bin-win-cuda-x64.zip",
        "-bin-win-x64.zip",
    ]

    valid_assets = [
        a for a in assets
        if a["name"].lower().startswith("llama-")
        and a["name"].lower().endswith((".zip", ".tar.gz"))
    ]

    if not valid_assets:
        raise RuntimeError(
            f"No pre-built binary asset found for {platform.system()} in release {tag}.\n"
            "Download llama-quantize manually from:\n"
            "  https://github.com/ggerganov/llama.cpp/releases\n"
            f"and place '{QUANTIZE_NAME}' inside: {PREBUILT_DIR}"
        )

    def sort_key(asset):
        name = asset["name"].lower()
        for i, suffix in enumerate(priorities):
            if name.endswith(suffix):
                return i
        return len(priorities)  # unmatched names tried last, not skipped

    candidates = sorted(valid_assets, key=sort_key)

    last_error = None
    for chosen_asset in candidates:
        archive_name = chosen_asset["name"]
        archive_path = WORK_DIR / archive_name

        try:
            urllib.request.urlretrieve(chosen_asset["browser_download_url"], archive_path)
            print(f"Download complete ({archive_path.stat().st_size / 1e6:.1f} MB)")

            if PREBUILT_DIR.exists():
                import shutil
                shutil.rmtree(PREBUILT_DIR, ignore_errors=True)
            PREBUILT_DIR.mkdir(exist_ok=True)

            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path) as zf:
                    zf.extractall(PREBUILT_DIR)
            else:
                with tarfile.open(archive_path) as tf:
                    tf.extractall(PREBUILT_DIR)

            try:
                archive_path.unlink()
            except Exception:
                pass

            found = _find_quantize_in_dir(PREBUILT_DIR)
            if found:
                if not IS_WINDOWS:
                    found.chmod(0o755)
                print(f"llama-quantize ready at {found}")
                return found

            print(f"'{QUANTIZE_NAME}' not in {archive_name}, trying next candidate ...")
        except Exception as e:
            last_error = e
            print(f"Failed with {archive_name}: {e}, trying next candidate ...")

    contents = [str(p) for p in PREBUILT_DIR.rglob("*")][:20] if PREBUILT_DIR.exists() else []
    raise RuntimeError(
        f"Tried {len(candidates)} release asset(s) but none contained '{QUANTIZE_NAME}'.\n"
        f"Last extracted dir contents (first 20): {contents}\n"
        f"Last error: {last_error}\n\n"
        "Download llama-quantize manually from:\n"
        "  https://github.com/ggerganov/llama.cpp/releases\n"
        f"and place '{QUANTIZE_NAME}' inside: {PREBUILT_DIR}"
    )

# Priority: prebuilt cache → alongside llama.cpp clone → download from GitHub
quantize_bin = _find_quantize_in_dir(PREBUILT_DIR) if PREBUILT_DIR.exists() else None

if quantize_bin is None:
    for candidate in [
        LLAMA_CPP_DIR / "build" / "bin" / QUANTIZE_NAME,
        LLAMA_CPP_DIR / QUANTIZE_NAME,
        LLAMA_CPP_DIR / "quantize",
        LLAMA_CPP_DIR / "quantize.exe",
    ]:
        if candidate.exists():
            quantize_bin = candidate
            break

if quantize_bin is None:
    print("llama-quantize binary not found — downloading pre-built release ...")
    quantize_bin = _download_prebuilt_quantize()

run([str(quantize_bin), str(GGUF_FP16_PATH), str(OUTPUT_GGUF_PATH), QUANT_TYPE])

size_gb = OUTPUT_GGUF_PATH.stat().st_size / 1e9

print(f"\n{'=' * 70}")
print("ALL DONE!")
print(f"{'=' * 70}")

print(f"\n  Final model : {OUTPUT_GGUF_PATH}")
print(f"  File size   : {size_gb:.2f} GB")

print("  Copy to server:")
print(f"    scp {OUTPUT_GGUF_PATH} \\")
