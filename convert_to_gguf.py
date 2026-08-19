"""
convert_to_gguf.py
==================
Run this script on a machine with enough RAM/disk (your PC, NOT the server).

Steps performed automatically:
  1. Download base model from Hugging Face (cached locally).
  2. Download LoRA adapter from Hugging Face (cached locally).
  3. Merge adapter into base model → saves full HF checkpoint.
  4. Clone llama.cpp (or reuse existing clone) for the conversion tools.
  5. Install llama.cpp Python conversion requirements.
  6. Convert merged HF model → GGUF (fp16 intermediate).
  7. Quantize GGUF to Q4_K_M (~1 GB for 1.5B model → fits in ~1.2 GB RAM).
  8. Place the final .gguf file in OUTPUT_GGUF_PATH.

After this script finishes, copy ONLY the produced .gguf file to the server:
    scp backend/app/.cache/models/model_q4km.gguf user@server:~/DevLegacy/backend/app/.cache/models/

─────────────────────────────────────────────────────────────────────────────
CHANGE ONLY THESE TWO LINES TO SWAP MODELS IN THE FUTURE:
─────────────────────────────────────────────────────────────────────────────
"""

# ── ✏️  CONFIGURE YOUR MODELS HERE ───────────────────────────────────────────
BASE_MODEL_REPO    = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
ADAPTER_MODEL_REPO = "sujalgawas/qwen2.5-coder-1.5b-code-reviewer"
# ─────────────────────────────────────────────────────────────────────────────

# Quantization type — Q4_K_M is the best quality/size trade-off for low RAM
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

# ── Final output — this is where the server will look for the model ──────────
OUTPUT_GGUF_PATH = SCRIPT_DIR / "backend" / "app" / ".cache" / "models" / "model_q4km.gguf"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def run(cmd: list, cwd=None):
    """Run a shell command, stream output, raise on failure."""
    print(f"\n  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def pip_install(*packages: str):
    run([sys.executable, "-m", "pip", "install", "--quiet", *packages])


# ─────────────────────────────────────────────────────────────────────────────
# Step 0 — ensure dependencies
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("STEP 0 — Installing / verifying Python dependencies")
print("=" * 70)

pip_install(
    "torch",
    "transformers",
    "peft",
    "huggingface_hub",
    "sentencepiece",
    "gguf",
    "numpy",
)

from huggingface_hub import login, snapshot_download  # noqa: E402
from transformers import AutoTokenizer, AutoModelForCausalLM  # noqa: E402
from peft import PeftModel  # noqa: E402
import torch  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Step 0b — HF login (optional — only needed for private models)
# ─────────────────────────────────────────────────────────────────────────────

hf_token = os.environ.get("HUGGING_FACE_TOKEN") or os.environ.get("HF_TOKEN")
if hf_token:
    login(token=hf_token)
    print("  ✔  Logged in to Hugging Face")
else:
    print("  ⚠  No HF token in env (HUGGING_FACE_TOKEN / HF_TOKEN).")
    print("     Set it if the models are private and re-run.")


WORK_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Download base model
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print(f"STEP 1 — Downloading base model: {BASE_MODEL_REPO}")
print("=" * 70)

if BASE_DIR.exists() and any(BASE_DIR.iterdir()):
    print(f"  ✔  Already cached at {BASE_DIR}")
else:
    snapshot_download(repo_id=BASE_MODEL_REPO, local_dir=str(BASE_DIR))
    print(f"  ✔  Saved to {BASE_DIR}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Download LoRA adapter
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print(f"STEP 2 — Downloading LoRA adapter: {ADAPTER_MODEL_REPO}")
print("=" * 70)

if ADAPTER_DIR.exists() and any(ADAPTER_DIR.iterdir()):
    print(f"  ✔  Already cached at {ADAPTER_DIR}")
else:
    snapshot_download(repo_id=ADAPTER_MODEL_REPO, local_dir=str(ADAPTER_DIR))
    print(f"  ✔  Saved to {ADAPTER_DIR}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Merge base + LoRA adapter and save full HF model
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("STEP 3 — Merging base + LoRA adapter")
print("=" * 70)

if MERGED_HF_DIR.exists() and any(MERGED_HF_DIR.iterdir()):
    print(f"  ✔  Already merged at {MERGED_HF_DIR}")
else:
    print("  Loading base model …")
    tokenizer = AutoTokenizer.from_pretrained(str(BASE_DIR))

    base_model = AutoModelForCausalLM.from_pretrained(
        str(BASE_DIR),
        torch_dtype=torch.float16,  # float16 on CPU is fine for merging/saving
        low_cpu_mem_usage=True,
        device_map="cpu",
    )

    print("  Applying LoRA adapter …")
    peft_model = PeftModel.from_pretrained(
        base_model,
        str(ADAPTER_DIR),
        is_trainable=False,
    )

    print("  Merging weights …")
    merged = peft_model.merge_and_unload()
    merged.eval()

    print(f"  Saving merged model to {MERGED_HF_DIR} …")
    MERGED_HF_DIR.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(MERGED_HF_DIR), safe_serialization=True)
    tokenizer.save_pretrained(str(MERGED_HF_DIR))

    # Free RAM before conversion step
    del merged, peft_model, base_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    import gc; gc.collect()

    print(f"  ✔  Merged model saved to {MERGED_HF_DIR}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Clone / update llama.cpp
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("STEP 4 — Setting up llama.cpp conversion tools")
print("=" * 70)

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

req_file = LLAMA_CPP_DIR / "requirements.txt"
if req_file.exists():
    pip_install("-r", str(req_file))

print("  ✔  llama.cpp ready")


# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — Convert merged HF model → fp16 GGUF
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("STEP 5 — Converting merged HF model → fp16 GGUF")
print("=" * 70)

# llama.cpp renamed the script over time; handle both
convert_script = LLAMA_CPP_DIR / "convert_hf_to_gguf.py"
if not convert_script.exists():
    convert_script = LLAMA_CPP_DIR / "convert.py"

if not convert_script.exists():
    print("ERROR: Could not find convert_hf_to_gguf.py or convert.py in llama.cpp.")
    sys.exit(1)

if GGUF_FP16_PATH.exists():
    print(f"  ✔  fp16 GGUF already exists at {GGUF_FP16_PATH}, skipping")
else:
    run([
        sys.executable, str(convert_script),
        str(MERGED_HF_DIR),
        "--outfile", str(GGUF_FP16_PATH),
        "--outtype", "f16",
    ])
    print(f"  ✔  fp16 GGUF saved to {GGUF_FP16_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 6 — Quantize to Q4_K_M using llama-quantize
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print(f"STEP 6 — Quantizing to {QUANT_TYPE}")
print("=" * 70)

OUTPUT_GGUF_PATH.parent.mkdir(parents=True, exist_ok=True)

# Locate the llama-quantize binary (build first if missing)
quantize_bin = LLAMA_CPP_DIR / "build" / "bin" / "llama-quantize"
if not quantize_bin.exists():
    quantize_bin = LLAMA_CPP_DIR / "quantize"  # older path

if not quantize_bin.exists():
    print("  llama-quantize binary not found — building llama.cpp …")
    build_dir = LLAMA_CPP_DIR / "build"
    build_dir.mkdir(exist_ok=True)
    run(["cmake", ".."], cwd=build_dir)
    run(["cmake", "--build", ".", "--config", "Release", "-j4"], cwd=build_dir)
    quantize_bin = build_dir / "bin" / "llama-quantize"
    if not quantize_bin.exists():
        quantize_bin = LLAMA_CPP_DIR / "quantize"

run([str(quantize_bin), str(GGUF_FP16_PATH), str(OUTPUT_GGUF_PATH), QUANT_TYPE])


# ─────────────────────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────────────────────

size_gb = OUTPUT_GGUF_PATH.stat().st_size / 1e9

print(f"\n{'=' * 70}")
print("  ✅  ALL DONE!")
print(f"{'=' * 70}")
print(f"\n  Final model : {OUTPUT_GGUF_PATH}")
print(f"  File size   : {size_gb:.2f} GB")
print()
print("  Copy to server:")
print(f"    scp {OUTPUT_GGUF_PATH} \\")
print(f"        user@yourserver:~/DevLegacy/backend/app/.cache/models/")
print()
print("  The server loads it automatically from that path.")
