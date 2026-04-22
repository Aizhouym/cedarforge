# Repair Loop Design

This document tracks the design evolution of the verifier-guided repair loop in CedarForge.

---

## v1 — Flat Feedback (superseded)

**Implemented in:** `run_baseline.py` — `_render_failure_feedback()`, `_build_repair_prompt()`

**Mechanism:**
- All stage results (syntax, schema, semantic) are flattened into a single text block
- Raw verifier errors and counterexamples are truncated and concatenated
- The same `repair.md` template is used regardless of which layer failed
- No history is passed across iterations

**Known problems:**
- No error-type prioritization: syntax and semantic errors appear together, confusing the model
- No directional signal: ceiling vs floor failures require opposite fixes; the model cannot tell which direction to move
- No cross-iteration memory: the model cannot detect that it is oscillating or that a previously-passing check has regressed
- Observed result: error oscillation (syntax ↔ semantic cycling) on `max_iterations=10` runs

---

## v2 — Layered, Directional, Memory-Aware Feedback (implemented)

**Status:** Fully implemented in `run_baseline.py`.

### What was built

#### 1. Strict layer prioritization

Only the highest-priority failing layer is surfaced per iteration.

Priority: `syntax > schema > semantic`

Rationale: `cedar symcc` is not run on syntactically invalid policies. Semantic counterexamples shown while syntax is broken may be stale or misleading.

#### 2. Error-type-specific repair prompts

Three separate prompt templates, each targeting a specific failure layer:
- `repair_syntax.md`: fix the specific token/expression; preserve all policy logic
- `repair_schema.md`: fix entity type, attribute, or action identifiers not in the schema
- `repair_semantic.md`: reference policy + counterexample + directional hint

#### 3. Directional hints for semantic failures

For each failing semantic check the repair prompt includes:
- **Direction**: `implies` fail → "TIGHTEN — your policy permits requests the ceiling forbids"; `floor` fail → "RELAX — your policy denies requests the floor requires"
- **Reference policy**: full Cedar text of the violated ceiling/floor (`references/<check_name>.cedar`)
- **Counterexample**: the specific request that exposed the violation

#### 4. Oscillation detection (`_is_oscillating`)

Tracked per iteration:
- `candidate_hashes`: SHA-256 of each candidate. Identical to previous → stuck.
- `failure_layer_sequence`: list of per-iteration failing layers. Detects `syntax → semantic → syntax` cycling.

`OSCILLATION_THRESHOLD = 6`: loop stops with `stop_reason="oscillation_no_progress"` after 6 oscillations.

When oscillation is detected, an explicit warning is prepended to the repair feedback:
> "WARNING: Oscillation detected (#N). You have been alternating between error types without converging. Rules: fix syntax FIRST, then address semantic issues separately."

#### 5. Best-so-far tracking

Maintains the best candidate across all iterations, defined as: syntax-passing AND lowest loss (fewest failed semantic checks). Stored in `best_candidate`, reported in `summary.json`.

#### 6. Temperature split

- Iteration 1 (initial generation): caller-supplied temperature (default `0.0`)
- Iterations 2+ (repair): fixed `REPAIR_TEMPERATURE = 0.4`

**Why:** At `temperature=0` the model is fully deterministic. The same wrong candidate is produced every iteration regardless of feedback; the oscillation detector triggers immediately and shuts down the loop. `0.4` gives enough stochasticity to explore alternative candidates while staying coherent on a constrained Cedar generation task. Values above `0.5` risk hallucinating schema elements.

**Observed failure (2026-04-09):** 10 consecutive runs on `clinical_trial` all hit `oscillation_no_progress` at iteration 6 with `failure_layer_sequence = ['syntax', 'syntax', ...]` at `temperature=0`. Fixed by the temperature split.

---

## v3 — Multi-Turn Conversation History (implemented)

**Status:** Implemented in `run_baseline.py`. Replaces the stateless single-turn repair of v2.

### Motivation

In v2 (single-turn), each repair iteration builds a fresh standalone prompt:

```
[system] + [schema + spec + previous_candidate + feedback]
```

The model sees the history only by reading its own prior output pasted into the prompt. This has two problems:
1. The prompt grows with each iteration (schema + spec repeated every turn).
2. The model has no conversational context — it cannot reason about *why* previous attempts failed in sequence.

In v3 (multi-turn), the conversation history is maintained as a real message list:

```
messages[0]  = {"role": "system",    "content": SYSTEM_MESSAGE}
messages[1]  = {"role": "user",      "content": initial_prompt}  # schema + spec, sent once
messages[2]  = {"role": "assistant", "content": <iter 1 output>}
messages[3]  = {"role": "user",      "content": <iter 2 feedback only>}
messages[4]  = {"role": "assistant", "content": <iter 2 output>}
...
```

Repair iterations only send feedback (no schema/spec repeat), since those are already in the history. This is implemented in `_build_repair_feedback()`.

### Context management: `_trim_messages`

To keep total tokens within the vLLM context limit (`--max-model-len 20480`):

```python
CONVERSATION_HISTORY_TURNS = 3  # keep last 3 turns = 6 messages

def _trim_messages(messages):
    keep_tail = CONVERSATION_HISTORY_TURNS * 2
    if len(messages) <= 2 + keep_tail:
        return messages
    return messages[:2] + messages[-keep_tail:]
```

- Always keeps `messages[0]` (system) and `messages[1]` (initial prompt with schema/spec).
- Keeps the last 3 turns (6 messages) of repair history.
- Earlier turns are dropped to stay within context.

**Token budget (estimated):** initial prompt ~2500t + 3 turns × ~3650t (output 2650t + feedback 1000t) + 4096 output ≈ 17,600t, within 20480. Tags scenarios were the driver: their outputs are ~2650t (measured), which exceeds the previous 2048 max_tokens limit and caused truncation.

### Repair feedback format (`_build_repair_feedback`)

```
--- Iteration N Feedback ---
[OSCILLATION_WARNING if triggered]

<layered failure feedback from _render_failure_feedback>

Please provide a corrected Cedar policy.
```

Schema and spec are not repeated — the model already has them from `messages[1]`.

### Key differences from v2

| | v2 (single-turn) | v3 (multi-turn) |
|---|---|---|
| Schema/spec per iteration | Repeated every turn | Sent once (messages[1]) |
| Repair feedback | Standalone prompt via `_build_repair_prompt` | Feedback-only message via `_build_repair_feedback` |
| Model sees prior attempts | Via pasted `PREVIOUS_CANDIDATE` | Via conversation history |
| Context growth | Linear in tokens per turn | Bounded by `_trim_messages` |
| Max iterations | Was 5, now **20** | 20 |
| Oscillation threshold | 6 | 6 (unchanged) |

### vLLM serving requirement

Multi-turn with `max_iterations=20` requires `--max-model-len 20480`:

```bash
vllm serve ~/model/cedar-qwen35b-runE \
  --served-model-name cedar-qwen35b \
  --port 8002 \
  --max-model-len 20480 \
  --trust-remote-code
```

The default `--max-model-len 8192` is insufficient for complex scenarios at 20 iterations. 16384 is also insufficient when `max_tokens=4096` and 3 turns of tags-scenario history are in context (~17,600t worst case).
