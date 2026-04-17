#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat <<'EOF'
launch.sh is now a compatibility wrapper.
Use run_experiments.sh with experiments.conf instead.

Examples:
  bash sft_gen/finetune/run_experiments.sh --list
  bash sft_gen/finetune/run_experiments.sh --run A
  bash sft_gen/finetune/run_experiments.sh --run A --eval
EOF

exec bash "${SCRIPT_DIR}/run_experiments.sh" "$@"
