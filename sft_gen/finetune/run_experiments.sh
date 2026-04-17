#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CEDARFORGE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TRAIN_SCRIPT="${SCRIPT_DIR}/train.py"
EVAL_SCRIPT="${SCRIPT_DIR}/evaluate.py"

CONFIG_PATH="${SCRIPT_DIR}/experiments.conf"
SELECTED_RUNS=()
DO_EVAL_OVERRIDE=""
SKIP_TRAIN=0
LIST_ONLY=0

usage() {
    cat <<'EOF'
Usage:
  bash sft_gen/finetune/run_experiments.sh [options]

Options:
  --config PATH       Hyperparameter config file to source
  --run ID            Run one specific experiment from the config (repeatable)
  --eval              Force evaluation after training
  --skip-train        Only run evaluation
  --list              Print configured experiments and exit
  -h, --help          Show help

Default config:
  sft_gen/finetune/experiments.conf

Typical workflow:
  1. Edit experiments.conf
  2. Run one experiment:
     bash sft_gen/finetune/run_experiments.sh --run A
  3. Run all configured experiments:
     bash sft_gen/finetune/run_experiments.sh
  4. Evaluate an existing adapter only:
     bash sft_gen/finetune/run_experiments.sh --run A --skip-train --eval
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config) CONFIG_PATH="$2"; shift 2 ;;
        --run) SELECTED_RUNS+=("$2"); shift 2 ;;
        --eval) DO_EVAL_OVERRIDE=1; shift ;;
        --skip-train) SKIP_TRAIN=1; shift ;;
        --list) LIST_ONLY=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
    esac
done

if [[ ! -f "${CONFIG_PATH}" ]]; then
    echo "Config file not found: ${CONFIG_PATH}" >&2
    exit 1
fi

# shellcheck disable=SC1090
source "${CONFIG_PATH}"

if [[ -z "${BASE_MODEL:-}" ]]; then
    echo "Config must define BASE_MODEL" >&2
    exit 1
fi

if [[ -z "${RUN_IDS+x}" ]]; then
    echo "Config must define RUN_IDS=(...)" >&2
    exit 1
fi

TRAIN_FILE="${TRAIN_FILE:-${SCRIPT_DIR}/data/train.jsonl}"
VAL_FILE="${VAL_FILE:-${SCRIPT_DIR}/data/val.jsonl}"
VAL_META_FILE="${VAL_META_FILE:-${SCRIPT_DIR}/data/val.meta.jsonl}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${SCRIPT_DIR}/checkpoints}"
PREPARE_DATA="${PREPARE_DATA:-1}"
EVAL_AFTER_TRAIN="${EVAL_AFTER_TRAIN:-0}"
MASTER_PORT_BASE="${MASTER_PORT_BASE:-29500}"

cfg() {
    local run_id="$1"
    local field="$2"
    local default_value="${3:-}"
    local var_name="RUN_${run_id}_${field}"
    printf '%s' "${!var_name:-$default_value}"
}

print_run_summary() {
    local run_id="$1"
    local name gpus batch accum epochs lr rank lazy output_dir
    name="$(cfg "${run_id}" NAME "${run_id}")"
    gpus="$(cfg "${run_id}" GPUS)"
    batch="$(cfg "${run_id}" BATCH)"
    accum="$(cfg "${run_id}" ACCUM)"
    epochs="$(cfg "${run_id}" EPOCHS)"
    lr="$(cfg "${run_id}" LR)"
    rank="$(cfg "${run_id}" RANK)"
    lazy="$(cfg "${run_id}" DISABLE_LAZY_NO_MMAP 0)"
    output_dir="$(cfg "${run_id}" OUTPUT_DIR "${OUTPUT_ROOT}/run_${run_id}")"
    echo "${run_id} | ${name} | gpus=${gpus} batch=${batch} accum=${accum} epochs=${epochs} lr=${lr} rank=${rank} lazy_no_mmap=$((1-lazy)) output=${output_dir}"
}

run_eval() {
    local run_id="$1"
    local output_dir adapter
    output_dir="$(cfg "${run_id}" OUTPUT_DIR "${OUTPUT_ROOT}/run_${run_id}")"
    adapter="${output_dir}/final_adapter"

    if [[ ! -d "${adapter}" ]]; then
        echo "Skip eval for ${run_id}: adapter not found at ${adapter}" >&2
        return 0
    fi

    echo ""
    echo "------------------------------------------------------------"
    echo "Evaluating ${run_id}"
    echo "Adapter: ${adapter}"
    echo "------------------------------------------------------------"

    (
        cd "${CEDARFORGE_DIR}"
        python "${EVAL_SCRIPT}" \
            --adapter "${adapter}" \
            --base-model "${BASE_MODEL}" \
            --val-file "${VAL_META_FILE}"
    )
}

run_train() {
    local run_id="$1"
    local name output_dir gpus batch accum epochs lr rank dropout alpha max_seq_len use_qlora disable_lazy master_port
    name="$(cfg "${run_id}" NAME "${run_id}")"
    output_dir="$(cfg "${run_id}" OUTPUT_DIR "${OUTPUT_ROOT}/run_${run_id}")"
    gpus="$(cfg "${run_id}" GPUS)"
    batch="$(cfg "${run_id}" BATCH)"
    accum="$(cfg "${run_id}" ACCUM)"
    epochs="$(cfg "${run_id}" EPOCHS)"
    lr="$(cfg "${run_id}" LR)"
    rank="$(cfg "${run_id}" RANK)"
    dropout="$(cfg "${run_id}" LORA_DROPOUT 0.05)"
    alpha="$(cfg "${run_id}" ALPHA "$(( rank * 2 ))")"
    max_seq_len="$(cfg "${run_id}" MAX_SEQ_LEN 4096)"
    use_qlora="$(cfg "${run_id}" USE_QLORA 0)"
    disable_lazy="$(cfg "${run_id}" DISABLE_LAZY_NO_MMAP 0)"
    master_port="$(cfg "${run_id}" MASTER_PORT "$(( MASTER_PORT_BASE + 10#${run_id//[!0-9]/0} ))")"

    if [[ -z "${gpus}" || -z "${batch}" || -z "${accum}" || -z "${epochs}" || -z "${lr}" || -z "${rank}" ]]; then
        echo "Run ${run_id} is missing one of required fields: GPUS/BATCH/ACCUM/EPOCHS/LR/RANK" >&2
        exit 1
    fi

    echo ""
    echo "============================================================"
    echo "Training ${run_id} (${name})"
    echo "Output: ${output_dir}"
    echo "============================================================"

    train_args=(
        --model-path "${BASE_MODEL}"
        --train-file "${TRAIN_FILE}"
        --val-file "${VAL_FILE}"
        --output-dir "${output_dir}"
        --lora-rank "${rank}"
        --lora-alpha "${alpha}"
        --lora-dropout "${dropout}"
        --lr "${lr}"
        --epochs "${epochs}"
        --per-device-batch "${batch}"
        --grad-accum "${accum}"
        --max-seq-len "${max_seq_len}"
    )

    if [[ "${use_qlora}" == "1" ]]; then
        train_args+=(--use-qlora)
    fi
    if [[ "${disable_lazy}" == "1" ]]; then
        train_args+=(--disable-lazy-no-mmap)
    fi

    (
        cd "${CEDARFORGE_DIR}"
        if [[ "${PREPARE_DATA}" == "1" ]]; then
            python sft_gen/finetune/prepare_data.py
        fi
        torchrun \
            --nproc_per_node="${gpus}" \
            --master_port="${master_port}" \
            "${TRAIN_SCRIPT}" \
            "${train_args[@]}"
    )
}

if [[ ${#SELECTED_RUNS[@]} -eq 0 ]]; then
    SELECTED_RUNS=("${RUN_IDS[@]}")
fi

echo "Config: ${CONFIG_PATH}"
echo "Base model: ${BASE_MODEL}"
echo "Train file: ${TRAIN_FILE}"
echo "Val file: ${VAL_FILE}"
echo "Selected experiments:"
for run_id in "${SELECTED_RUNS[@]}"; do
    print_run_summary "${run_id}"
done

if [[ "${LIST_ONLY}" == "1" ]]; then
    exit 0
fi

for run_id in "${SELECTED_RUNS[@]}"; do
    if [[ "${SKIP_TRAIN}" != "1" ]]; then
        run_train "${run_id}"
    fi

    eval_flag="${DO_EVAL_OVERRIDE:-$EVAL_AFTER_TRAIN}"
    if [[ "${eval_flag}" == "1" ]]; then
        run_eval "${run_id}"
    fi
done

echo ""
echo "Done."
