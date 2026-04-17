#!/usr/bin/env python3
"""Evaluate a fine-tuned Qwen3.5B MoE adapter on the val set.

Runs the model on each val scenario's (schema, spec) prompt and:
  1. Writes the generated candidate.cedar to a temp workspace.
  2. Runs `cedar validate` on it — checks syntactic validity.
  3. Runs the orchestrator (symcc) against the scenario's verification plan.
  4. Reports pass rate.

Usage (from cedarforge/ directory):
    conda activate vllm
    python sft_gen/finetune/evaluate.py \
        --adapter sft_gen/finetune/checkpoints/final_adapter \
        --base-model /home/yzhou136/model/qwen35b-full

Or against the base model (zero-shot baseline):
    python sft_gen/finetune/evaluate.py --base-model /home/yzhou136/model/qwen35b-full
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def _patch_safe_open_no_mmap() -> None:
    """Replace safetensors mmap loader with a heap read()-based loader.

    Avoids ENOMEM on HPC nodes where vm.overcommit_memory=2 blocks large mmap calls.
    Reads each tensor's bytes via seek+read() instead of mmap().
    """
    import json, struct
    from pathlib import Path as _Path

    class _Slice:
        _DTYPE = {"F32": torch.float32, "F16": torch.float16, "BF16": torch.bfloat16,
                  "I32": torch.int32, "I64": torch.int64, "I8": torch.int8, "U8": torch.uint8}
        def __init__(self, path, offset, length, shape, dtype_str):
            self._path, self._offset, self._length = path, offset, length
            self._shape, self._dtype_str = shape, dtype_str
        def get_shape(self): return self._shape
        def get_dtype(self): return self._dtype_str
        def __getitem__(self, idx):
            dtype = self._DTYPE.get(self._dtype_str, torch.float32)
            with open(self._path, "rb") as fh:
                fh.seek(self._offset)
                buf = bytearray(fh.read(self._length))
            return torch.frombuffer(buf, dtype=dtype).reshape(self._shape).clone()[idx]

    class _SafeOpen:
        def __init__(self, path, framework="pt", device="cpu"):
            self._path = path
            with open(path, "rb") as fh:
                hdr_len = struct.unpack("<Q", fh.read(8))[0]
                hdr = json.loads(fh.read(hdr_len))
                self._data_start = 8 + hdr_len
            self._meta = hdr.pop("__metadata__", {})
            self._info = {k: {"dtype": v["dtype"], "shape": v["shape"],
                               "offset": self._data_start + v["data_offsets"][0],
                               "length": v["data_offsets"][1] - v["data_offsets"][0]}
                          for k, v in hdr.items()}
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def keys(self): return list(self._info.keys())
        def metadata(self): return self._meta
        def offset_keys(self): return []
        def get_tensor(self, key): return self.get_slice(key)[...]
        def get_slice(self, key):
            i = self._info[key]
            return _Slice(self._path, i["offset"], i["length"], i["shape"], i["dtype"])

    import transformers.modeling_utils as _mu
    _mu.safe_open = _SafeOpen

_HERE = Path(__file__).resolve().parent
_CEDARFORGE = _HERE.parent.parent
_REPO_ROOT = _CEDARFORGE.parent
SCENARIOS_DIR = _HERE.parent / "scenarios"
DATA_DIR = _HERE / "data"

DEFAULT_MODEL = "/home/yzhou136/model/qwen35b-full"
def _find_bin(name: str) -> str:
    """Find binary: env var > conda active env > anaconda3/envs/vllm fallback."""
    import shutil
    if name.upper() in os.environ:
        return os.environ[name.upper()]
    found = shutil.which(name)
    if found:
        return found
    return str(Path.home() / f"anaconda3/envs/vllm/bin/{name}")

CEDAR_BIN = _find_bin("cedar")
CVC5_BIN  = _find_bin("cvc5")


def load_model(base_model: str, adapter: str | None):
    tokenizer = AutoTokenizer.from_pretrained(
        base_model, trust_remote_code=True, padding_side="left"
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    _patch_safe_open_no_mmap()
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        trust_remote_code=True,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
        device_map="auto",
        low_cpu_mem_usage=True,
    )

    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)
        print(f"Loaded adapter: {adapter}")
    else:
        print("Running base model (no adapter — zero-shot baseline)")

    model.eval()
    return model, tokenizer


SFT_SYSTEM = """\
You are an expert Cedar access-control policy synthesizer. Given a Cedar schema \
and a natural-language policy specification, write the Cedar policies that \
exactly implement the specification.

Rules:
- Cedar denies by default; write only permit and forbid rules.
- forbid always overrides permit.
- Use unless { ... } for exceptions to forbid rules.
- Optional attributes: always has-guard before reading.
- Set containment: set.contains(value), NOT value in set.
- datetime uses ISO 8601; duration uses Go-style (1h, -24h, 1h30m).

Output Format:
Only output the final Cedar policy inside <cedar_policy> tags.

<cedar_policy>
Cedar policy here
</cedar_policy>\
"""


def build_user_message(schema: str, spec: str) -> str:
    return (
        "## Cedar Schema\n"
        "```cedar\n"
        f"{schema.strip()}\n"
        "```\n\n"
        "## Policy Specification\n"
        f"{spec.strip()}\n\n"
        "Write the Cedar policies now."
    )


def generate(model, tokenizer, schema: str, spec: str, max_new_tokens: int = 4096) -> str:
    messages = [
        {"role": "system", "content": SFT_SYSTEM},
        {"role": "user",   "content": build_user_message(schema, spec)},
    ]
    # Build prompt manually — no <think> tokens, matching the training data format.
    user_content = build_user_message(schema, spec)
    text = (
        f"<|im_start|>system\n{SFT_SYSTEM}<|im_end|>\n"
        f"<|im_start|>user\n{user_content}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    inputs = tokenizer(text, add_special_tokens=False, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output_ids[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(generated, skip_special_tokens=True).strip()

    import re
    # Extract content from <cedar_policy>...</cedar_policy> tags.
    # This is immune to <think> blocks, markdown fences, and surrounding prose.
    m = re.search(r"<cedar_policy>\s*(.*?)\s*</cedar_policy>", text, flags=re.DOTALL)
    if m:
        return m.group(1).strip()

    # Fallback for models not trained on tagged format: take everything after </think>,
    # or find the first permit/forbid statement.
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    else:
        permit_m = re.search(r'(permit|forbid)\s*[\(\n]', text)
        if permit_m:
            text = text[permit_m.start():]

    text = re.sub(r"^```(?:cedar)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text).strip()
    return text


def cedar_validate(schema_path: Path, policy_path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [CEDAR_BIN, "validate", "--schema", str(schema_path), "--policies", str(policy_path)],
        capture_output=True, text=True, timeout=30,
    )
    ok = result.returncode == 0
    return ok, (result.stdout + result.stderr).strip()


def run_orchestrator(scenario_dir: Path, candidate_path: Path) -> tuple[bool, int]:
    """Copy candidate to workspace, run orchestrator, return (pass, loss)."""
    # orchestrator reads candidate.cedar from the workspace dir
    import shutil
    workspace = scenario_dir  # orchestrator reads from scenario dir directly
    tmp_candidate = workspace / "candidate.cedar"
    shutil.copy(candidate_path, tmp_candidate)

    env = os.environ.copy()
    env["CVC5"] = CVC5_BIN
    result = subprocess.run(
        ["python", "orchestrator.py", "--workspace", str(workspace)],
        capture_output=True, text=True, timeout=120, cwd=str(_REPO_ROOT), env=env,
    )
    output = result.stdout + result.stderr
    # Parse loss from output
    loss = None
    for line in output.splitlines():
        if "loss:" in line:
            try:
                loss = int(line.split("loss:")[-1].strip().split()[0])
            except ValueError:
                pass
    passed = loss == 0
    return passed, loss if loss is not None else -1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default=DEFAULT_MODEL)
    parser.add_argument("--adapter",    default=None,
                        help="Path to LoRA adapter dir (omit for zero-shot baseline)")
    parser.add_argument("--val-file",   default=str(DATA_DIR / "val.meta.jsonl"))
    parser.add_argument("--skip-symcc", action="store_true",
                        help="Only run cedar validate, skip symcc (faster)")
    parser.add_argument("--debug", action="store_true",
                        help="Dump raw model output (before post-processing) to a file and exit after first scenario")
    parser.add_argument("--debug-out", default="debug_output.txt",
                        help="File to write --debug output to (default: debug_output.txt)")
    args = parser.parse_args()

    model, tokenizer = load_model(args.base_model, args.adapter)

    records = [json.loads(l) for l in Path(args.val_file).open()]
    print(f"\nEvaluating {len(records)} val scenarios\n{'='*60}")

    results = []
    for rec in records:
        sid = rec["_meta"]["id"]
        scenario_dir = SCENARIOS_DIR / sid
        schema_text = (scenario_dir / "schema.cedarschema").read_text()
        spec_text   = (scenario_dir / "policy_spec.md").read_text()

        print(f"\n[{sid}]")

        if args.debug:
            # Print raw decode before any post-processing, then stop
            import torch, re as _re
            messages = [
                {"role": "system", "content": SFT_SYSTEM},
                {"role": "user",   "content": build_user_message(schema_text, spec_text)},
            ]
            user_content = build_user_message(schema_text, spec_text)
            text = (
                f"<|im_start|>system\n{SFT_SYSTEM}<|im_end|>\n"
                f"<|im_start|>user\n{user_content}<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            inputs = tokenizer(text, add_special_tokens=False, return_tensors="pt").to(model.device)
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs, max_new_tokens=4096, do_sample=False,
                    temperature=None, top_p=None,
                    pad_token_id=tokenizer.eos_token_id,
                )
            raw = tokenizer.decode(
                output_ids[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=False,
            )
            out_path = Path(args.debug_out)
            with out_path.open("w") as fh:
                fh.write(f"Scenario: {sid}\n")
                fh.write("="*60 + "\n")
                fh.write("RAW MODEL OUTPUT (special tokens visible, no post-processing)\n")
                fh.write("="*60 + "\n")
                fh.write(raw + "\n")
                fh.write("="*60 + "\n")
                fh.write(f"\nrepr (first 1000 chars):\n{repr(raw[:1000])}\n")
            print(f"  Raw output saved → {out_path.resolve()}")
            return

        generated = generate(model, tokenizer, schema_text, spec_text)

        with tempfile.NamedTemporaryFile(suffix=".cedar", mode="w", delete=False) as f:
            f.write(generated)
            tmp = Path(f.name)

        # 1. cedar validate
        valid, msg = cedar_validate(scenario_dir / "schema.cedarschema", tmp)
        print(f"  cedar validate: {'PASS' if valid else 'FAIL'}")
        if not valid:
            print(f"    {msg[:200]}")

        # 2. symcc verification
        symcc_pass, loss = False, -1
        if valid and not args.skip_symcc:
            symcc_pass, loss = run_orchestrator(scenario_dir, tmp)
            print(f"  symcc:         {'PASS' if symcc_pass else 'FAIL'}  loss={loss}")
        elif args.skip_symcc:
            symcc_pass = valid  # treat validate as proxy

        tmp.unlink(missing_ok=True)
        results.append({
            "id": sid,
            "cedar_valid": valid,
            "symcc_pass":  symcc_pass,
            "loss":        loss,
        })

    # Summary
    print(f"\n{'='*60}")
    n = len(results)
    n_valid  = sum(r["cedar_valid"] for r in results)
    n_symcc  = sum(r["symcc_pass"]  for r in results)
    print(f"cedar validate: {n_valid}/{n} ({100*n_valid//n}%)")
    print(f"symcc pass:     {n_symcc}/{n} ({100*n_symcc//n}%)")
    print()
    for r in results:
        status = "PASS" if r["symcc_pass"] else ("VALID" if r["cedar_valid"] else "FAIL")
        print(f"  {status:<6} {r['id']}")


if __name__ == "__main__":
    main()
