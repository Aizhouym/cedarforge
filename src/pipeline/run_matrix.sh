#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BASE_URL=""
MODEL=""
MAX_ITERATIONS="4"
EXPERIMENT=""
BENCHMARK="all"
MODES_CSV="single,repair"
VARIANTS_CSV="structured_instruction"
REPEATS="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --experiment)
      EXPERIMENT="$2"
      shift 2
      ;;
    --benchmark)
      BENCHMARK="$2"
      shift 2
      ;;
    --modes)
      MODES_CSV="$2"
      shift 2
      ;;
    --variants)
      VARIANTS_CSV="$2"
      shift 2
      ;;
    --repeats)
      REPEATS="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 --base-url <url> --model <name> --experiment <name> [--benchmark <all|mutations|realworld>] [--modes <single,repair>] [--variants <v1,v2>] [--repeats <n>] [--max-iterations <n>]"
      echo "Example: $0 --base-url http://localhost:8002/v1 --model qwen35b --experiment cedarbench_v1 --benchmark all --modes single,repair --variants structured_instruction --repeats 1 --max-iterations 5"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Usage: $0 --base-url <url> --model <name> --experiment <name> [--benchmark <all|mutations|realworld>] [--modes <single,repair>] [--variants <v1,v2>] [--repeats <n>] [--max-iterations <n>]"
      exit 1
      ;;
  esac
done

if [[ -z "${BASE_URL}" || -z "${MODEL}" || -z "${EXPERIMENT}" ]]; then
  echo "Missing required arguments."
  echo "Usage: $0 --base-url <url> --model <name> --experiment <name> [--benchmark <all|mutations|realworld>] [--modes <single,repair>] [--variants <v1,v2>] [--repeats <n>] [--max-iterations <n>]"
  exit 1
fi

if [[ -n "${TASKS:-}" ]]; then
  TASKS=(${TASKS})
else
  mapfile -t TASKS < <(python3 - <<PY
import pathlib
import sys

repo_root = pathlib.Path("${REPO_ROOT}")
sys.path.insert(0, str(repo_root / "cedarforge" / "src"))
from pipeline.run_baseline import _load_task_registry, _task_ids_for_benchmark

registry = _load_task_registry()
for task_id in _task_ids_for_benchmark(registry, "${BENCHMARK}"):
    print(task_id)
PY
)
fi
IFS=',' read -r -a VARIANTS <<< "${VARIANTS_CSV}"
IFS=',' read -r -a MODES <<< "${MODES_CSV}"

if [[ -f "${HOME}/anaconda3/etc/profile.d/conda.sh" ]]; then
  # shellcheck source=/dev/null
  source "${HOME}/anaconda3/etc/profile.d/conda.sh"
  conda activate vllm
fi

cd "${REPO_ROOT}"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "CONDA_PREFIX is not set. Activate the vllm environment first."
  exit 1
fi

echo "================================================================"
echo "EXPERIMENT: ${EXPERIMENT}"
echo "BENCHMARK:  ${BENCHMARK}"
echo "TASKS:      ${#TASKS[@]} tasks"
echo "VARIANTS:   ${VARIANTS[*]}"
echo "MODES:      ${MODES[*]}"
echo "REPEATS:    ${REPEATS}"
echo "MAX_ITER:   ${MAX_ITERATIONS}"
echo "MODEL:      ${MODEL}"
echo "BASE_URL:   ${BASE_URL}"
echo "================================================================"

for task in "${TASKS[@]}"; do
  for variant in "${VARIANTS[@]}"; do
    strategy_dir="${task}-${variant}"

    for mode in "${MODES[@]}"; do
      for repeat in $(seq 1 "${REPEATS}"); do
        timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
        if [[ "${mode}" == "repair" ]]; then
          run_prefix="repair_loop"
          run_suffix="${timestamp}_repair_mi$(printf '%02d' "${MAX_ITERATIONS}")"
        else
          run_prefix="no_repair_loop"
          run_suffix="${timestamp}_single"
        fi
        run_id="${run_prefix}/${EXPERIMENT}/${strategy_dir}/${run_suffix}"

        cmd=(
          python src/pipeline/run_baseline.py
          --task "${task}"
          --variant "${variant}"
          --base-url "${BASE_URL}"
          --model "${MODEL}"
          --run-id "${run_id}"
        )

        if [[ "${mode}" == "repair" ]]; then
          cmd+=(--mode repair --max-iterations "${MAX_ITERATIONS}")
        fi

        echo
        echo "================================================================"
        echo "task=${task} variant=${variant} mode=${mode} repeat=${repeat}/${REPEATS}"
        echo "run_id=${run_id}"
        echo "================================================================"

        CVC5="${CONDA_PREFIX}/bin/cvc5" "${cmd[@]}"
        sleep 1
      done
    done
  done
done
