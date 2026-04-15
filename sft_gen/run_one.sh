#!/usr/bin/env bash
# Run sft_program.md for one scenario via the Codex CLI.
#
# Usage:
#   ./sft_gen/run_one.sh github_sso_gate
#
# Requirements:
#   - codex CLI: npm install -g @openai/codex
#   - OPENAI_API_KEY set in environment

set -e

SCENARIO_ID="${1:?Usage: $0 <scenario_id>}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCENARIO_DIR="$REPO_ROOT/cedarforge/sft_gen/scenarios/$SCENARIO_ID"
PROGRAM_MD="$REPO_ROOT/cedarforge/sft_gen/sft_program.md"

if [ ! -d "$SCENARIO_DIR" ]; then
    echo "ERROR: $SCENARIO_DIR does not exist"
    echo "Run: python cedarforge/sft_gen/generate.py  first"
    exit 1
fi

echo "Scenario: $SCENARIO_DIR"

codex --approval-mode full-auto \
  "Read $PROGRAM_MD and execute it for this scenario directory: $SCENARIO_DIR"
