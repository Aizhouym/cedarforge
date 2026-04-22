# CedarBench Experiment Record

This document records CedarBench experiment settings and outcomes in a form that is easy to extend with future runs, including fine-tuned model evaluations.

## Scope

This page currently records the original `qwen35b` baselines and the current `qwen35B_runE` fine-tuned model under `cedarforge/src/runs`:

1. `no_repair_loop/cedarbench_single_qwen35b`
2. `repair_loop/cedarbench_repair_qwen35b`
3. `no_repair_loop/cedarbench_repair_qwen35b_runE`
4. `repair_loop/cedarbench_repair_qwen35b_runE`

The original `qwen35b` runs should be treated as baseline reference points for later comparisons against fine-tuned models and new prompting / repair strategies.

## Experiment Settings

| Setting | `no_repair_loop` | `repair_loop` |
|---|---|---|
| Run path | `cedarforge/src/runs/no_repair_loop/cedarbench_single_qwen35b` | `cedarforge/src/runs/repair_loop/cedarbench_repair_qwen35b` |
| Model | `qwen35b` | `qwen35b` |
| Prompt family | `structured_instruction` | `structured_instruction` + repair prompts |
| Generation mode | Single-shot generation | Iterative generation with repair |
| Repair budget | None | Up to 5 iterations |
| Success criterion | Final candidate passes verification | Any iteration reaches verification pass |
| Output granularity | One `summary.json` per task | One `summary.json` per task with iteration history |

## Summary Table

| Method | Task count | Passed tasks | Pass rate | Avg semantic accuracy | Avg runtime |
|---|---:|---:|---:|---:|---:|
| `qwen35b` no repair | 121 | 59 | 48.8% | 0.6074 | 10.826s |
| `qwen35b` repair loop | 120 | 76 | 63.3% | 0.7565 | 29.819s |
| `qwen35B_runE` no repair | 121 | 51 | 42.1% | 0.6245 | 6.071s |
| `qwen35B_runE` repair loop | 121 | 95 | 78.5% | 0.8210 | 9.327s |

Note: the original `qwen35b` repair-loop set is missing one task, `tags_add_fourth_dimension`, so some paired comparisons on repair runs use the 120 shared tasks.

## Fine-Tuned Model: `qwen35B_runE`

### Experiment Settings

| Setting | `qwen35B_runE` no repair | `qwen35B_runE` repair loop |
|---|---|---|
| Run path | `cedarforge/src/runs/no_repair_loop/cedarbench_repair_qwen35b_runE` | `cedarforge/src/runs/repair_loop/cedarbench_repair_qwen35b_runE` |
| Model | `qwen35B_runE` | `qwen35B_runE` |
| Prompt family | `structured_instruction` | `structured_instruction` + repair prompts |
| Generation mode | Single-shot generation | Iterative generation with repair |
| Repair budget | None | Up to 5 iterations |
| Success criterion | Final candidate passes verification | Any iteration reaches verification pass |
| Output granularity | One `summary.json` per task | One `summary.json` per task with iteration history |

### Main Result

The fine-tuned model shows a split outcome:

- Without repair, `qwen35B_runE` is weaker than the original `qwen35b` baseline on pass rate.
- With repair, `qwen35B_runE` is substantially stronger than the original `qwen35b` baseline.

This means the current fine-tuning appears to have produced a model that is more effective inside a verifier-guided repair workflow than in pure single-shot generation.

### Comparison Against Original `qwen35b`

| Comparison | Baseline | `qwen35B_runE` | Change |
|---|---:|---:|---:|
| No-repair passed tasks | 59/121 | 51/121 | -8 |
| No-repair pass rate | 48.8% | 42.1% | -6.7 points |
| No-repair avg semantic accuracy | 0.6074 | 0.6245 | +0.0171 |
| No-repair avg runtime | 10.826s | 6.071s | -4.755s |
| Repair-loop passed tasks | 76/120 | 95/121 | +19 raw tasks |
| Repair-loop pass rate | 63.3% | 78.5% | +15.2 points |
| Repair-loop avg semantic accuracy | 0.7565 | 0.8210 | +0.0645 |
| Repair-loop avg runtime | 29.819s | 9.327s | -20.492s |

### Interpretation Of The Fine-Tuning Effect

The current `runE` behavior suggests:

1. Fine-tuning did not improve single-shot stability.
2. Fine-tuning did improve repair responsiveness.
3. The strongest deployment setting for `qwen35B_runE` is repair loop, not no-repair generation.

In short, `qwen35B_runE` behaves more like a strong repair-oriented model than a stronger direct synthesis model.

### No-Repair Changes Relative To `qwen35b`

On the 121 shared no-repair tasks:

| Outcome from `qwen35b` no repair to `qwen35B_runE` no repair | Task count |
|---|---:|
| Fail -> Pass | 9 |
| Pass -> Pass | 42 |
| Fail -> Fail | 53 |
| Pass -> Fail | 17 |

Representative improvements:

- `api_key_scoped_access`
- `ci_cd_deployment_gate`
- `clinical_add_export`
- `clinical_remove_auditor`
- `delegation_temporary_grant`
- `doccloud_remove_public`
- `gdpr_data_retention`
- `sales_temporal_campaign`
- `tax_add_auditor`

Representative regressions:

- `clinical_add_sponsor`
- `clinical_base`
- `clinical_full_expansion`
- `doccloud_base`
- `github_add_private`
- `github_add_pullrequest`
- `github_no_archive`
- `sales_add_team`
- `tax_add_edit`
- `tax_remove_consent`

This is the clearest sign that fine-tuning did not help the direct one-shot setting overall.

### Repair-Loop Changes Relative To `qwen35b`

On the 120 shared repair-loop tasks:

| Outcome from `qwen35b` repair loop to `qwen35B_runE` repair loop | Task count |
|---|---:|
| Fail -> Pass | 27 |
| Pass -> Pass | 68 |
| Fail -> Fail | 17 |
| Pass -> Fail | 8 |

Representative improvements:

- `approval_chain_workflow`
- `clinical_add_consent`
- `clinical_add_study_phase`
- `delegation_temporary_grant`
- `doccloud_add_admin_group`
- `doccloud_add_expiry`
- `doccloud_add_version_lock`
- `doccloud_remove_blocking`
- `github_add_close_issue`
- `github_full_expansion`
- `github_pr_review_workflow`
- `hotel_temporal_rates`
- `hundred_check_scale`
- `sales_add_approval`
- `sales_add_delete`
- `sales_full_expansion`
- `streaming_add_age_rating`
- `streaming_add_geo_restriction`
- `streaming_multidevice`
- `streaming_parental_controls`
- `tax_add_sensitivity`
- `tax_full_expansion`

Regressions:

- `clinical_add_sponsor`
- `hotel_add_cancel`
- `hotel_add_franchise`
- `hotel_add_renovation_lock`
- `hotel_franchise_loyalty`
- `sales_add_regional_manager`
- `streaming_add_trial_tier`
- `subscription_content_gate`

Despite these regressions, the repair-loop net gain is strongly positive.

### Repair Loop Benefit Inside `qwen35B_runE`

Comparing the fine-tuned model with and without repair on the same 121 tasks:

| Outcome from `qwen35B_runE` no repair to `qwen35B_runE` repair loop | Task count |
|---|---:|
| Fail -> Pass | 45 |
| Pass -> Pass | 50 |
| Fail -> Fail | 25 |
| Pass -> Fail | 1 |

Only one task regresses under repair:

- `hotel_add_cancel`

This shows that repair is not optional for `qwen35B_runE`; it is the main reason the model performs well on CedarBench.

### `qwen35B_runE` Failure Breakdown And Repair Behavior

#### No-repair failure types

| Failure type | Task count |
|---|---:|
| `semantic` | 29 |
| `syntax` | 25 |
| `schema` | 16 |

#### Repair-loop iteration distribution

| Completed iterations | Task count |
|---|---:|
| 1 | 52 |
| 2 | 28 |
| 3 | 9 |
| 4 | 4 |
| 5 | 28 |

#### First success iteration

| First success iteration | Task count |
|---|---:|
| 1 | 52 |
| 2 | 28 |
| 3 | 9 |
| 4 | 4 |
| 5 | 2 |

#### Repair-loop stop reasons

| Stop reason | Task count |
|---|---:|
| `verification_pass` | 95 |
| `max_iterations_reached` | 19 |
| `oscillation_no_progress` | 7 |

#### Common stuck patterns after repair

| Pattern | Count |
|---|---:|
| `schema -> schema -> schema -> schema -> schema` | 10 |
| `syntax -> syntax -> syntax -> syntax -> syntax` | 8 |
| `semantic -> semantic -> semantic -> semantic -> semantic` | 3 |

These remaining failures suggest that the fine-tuned model has already recovered many medium-difficulty tasks, while the residual failures are more concentrated in stubborn schema and syntax loops.

## Paired Comparison On Shared Tasks

The table below compares only the 120 tasks that exist in both experiment folders.

| Outcome from `no_repair_loop` to `repair_loop` | Task count |
|---|---:|
| Fail -> Pass | 21 |
| Pass -> Pass | 55 |
| Fail -> Fail | 40 |
| Pass -> Fail | 4 |

On the shared task set, the repair loop produces a net improvement of 17 tasks.

## What The Repair Loop Improves

The repair loop mainly helps in three areas:

| Improvement area | Evidence |
|---|---|
| Syntax recovery | In the no-repair baseline, failures are dominated by syntax errors: 36 tasks. Repair raises final syntax pass count to 96/120. |
| Schema / validation recovery | Repair raises final schema pass count to 89/120 and rescues several schema-related failures. |
| Near-miss semantic correction | Some tasks that were close but incorrect in single-shot mode become full passes after repair. |

Examples of tasks improved by repair:

- `api_key_scoped_access`
- `clinical_add_export`
- `doccloud_graduated_sharing`
- `doccloud_org_isolation`
- `github_add_visibility`
- `sales_add_regional_manager`
- `streaming_add_trial_tier`
- `subscription_content_gate`
- `tax_add_auditor`
- `tax_add_supervisor`

## Iteration Behavior

Repair successes are usually early:

| First success iteration | Task count |
|---|---:|
| 1 | 58 |
| 2 | 8 |
| 3 | 5 |
| 4 | 3 |
| 5 | 2 |

Overall iteration distribution:

| Completed iterations | Task count |
|---|---:|
| 1 | 58 |
| 2 | 8 |
| 3 | 5 |
| 4 | 3 |
| 5 | 46 |

Stop reasons in `repair_loop`:

| Stop reason | Task count |
|---|---:|
| `verification_pass` | 76 |
| `max_iterations_reached` | 37 |
| `oscillation_no_progress` | 7 |

This shows that repair is effective when the model can be corrected quickly, but many hard tasks still consume the full repair budget.

## Failure Breakdown

### `no_repair_loop` failure types

| Failure type | Task count |
|---|---:|
| `syntax` | 36 |
| `semantic` | 18 |
| `schema` | 8 |

### Common repair-loop stuck patterns

| Pattern | Count |
|---|---:|
| `syntax -> syntax -> syntax -> syntax -> syntax` | 20 |
| `semantic -> semantic -> semantic -> semantic -> semantic` | 6 |
| `schema -> schema -> schema -> schema -> schema` | 3 |

These patterns suggest that repair helps most with local fixable errors, but repeated failure usually means the model is not restructuring the policy correctly.

## Limitations

| Limitation | Evidence |
|---|---|
| Higher cost | Average runtime increases from `10.826s` to `29.819s`. |
| Incomplete recovery | 40 shared tasks still fail in both settings. |
| Possible regressions | 4 tasks pass in single-shot mode but fail under repair. |
| Weakness on harder semantic tasks | Many full-budget failures remain semantic or mixed semantic/structural failures. |
| Oscillation | Some tasks stop with `oscillation_no_progress`, which means repair changed output without producing forward progress. |

The regressed tasks are:

- `approval_chain_workflow`
- `clinical_add_consent`
- `sales_add_team`
- `tax_add_sensitivity`

## Observed Improvement

Relative to `no_repair_loop`, the repair loop shows clear improvement:

- Pass count increases from 59 to 76.
- Pass rate increases from 48.8% to 63.3%.
- Average semantic accuracy increases from 0.6074 to 0.7565.
- Repair converts 21 shared-task failures into passes.

The main tradeoff is cost: the average runtime is about 2.75x higher.

## Interpretation

The current evidence suggests:

1. `repair_loop` is a stronger baseline than `no_repair_loop` for CedarBench under the same `qwen35b` model.
2. The repair loop is especially useful for syntax, schema, and near-miss verification failures.
3. The repair loop is not sufficient for the hardest tasks, especially cases that require deeper policy restructuring rather than local correction.
4. Future fine-tuned model experiments should be compared against both of these baselines, not only against the weaker single-shot configuration.

## Template For Future Experiments

Add future experiments using the same fields below.

### Experiment Metadata Template

| Field | Value |
|---|---|
| Experiment name |  |
| Run path |  |
| Model |  |
| Prompt family |  |
| Repair mode |  |
| Max iterations |  |
| Task count |  |
| Passed tasks |  |
| Pass rate |  |
| Avg semantic accuracy |  |
| Avg runtime |  |
| Notes |  |

### Comparison Template

| Method | Task count | Passed tasks | Pass rate | Avg semantic accuracy | Avg runtime |
|---|---:|---:|---:|---:|---:|
| `qwen35b` no repair baseline | 121 | 59 | 48.8% | 0.6074 | 10.826s |
| `qwen35b` repair baseline | 120 | 76 | 63.3% | 0.7565 | 29.819s |
| `qwen35B_runE` no repair | 121 | 51 | 42.1% | 0.6245 | 6.071s |
| `qwen35B_runE` repair | 121 | 95 | 78.5% | 0.8210 | 9.327s |
| `future_model_name` |  |  |  |  |  |

## Data Source

The numbers in this document were derived from per-task `summary.json` files under:

- `cedarforge/src/runs/no_repair_loop/cedarbench_single_qwen35b`
- `cedarforge/src/runs/repair_loop/cedarbench_repair_qwen35b`
- `cedarforge/src/runs/no_repair_loop/cedarbench_repair_qwen35b_runE`
- `cedarforge/src/runs/repair_loop/cedarbench_repair_qwen35b_runE`

---

## Fine-Tuned Models: runG / runH / runI (repair loop, max_iterations=20)

These three runs evaluate the next generation of fine-tuned models on all 121 CedarBench tasks using the updated multi-turn repair loop (v3) with `max_iterations=20`.

**Key changes from the runE experiments:**
- Repair loop upgraded from single-turn (stateless) to **multi-turn conversation history** — the model sees its own prior outputs and feedback across iterations.
- Max iterations increased from 5 to **20**.
- Oscillation threshold raised from 3 to **6**.
- Context trimming (`_trim_messages`): system + initial prompt + last 3 turns kept; earlier history dropped.

### Run paths

| Run | Path |
|---|---|
| runG | `cedarforge/src/runs/repair_loop/cedarbench_qwen35b_runG` |
| runH | `cedarforge/src/runs/repair_loop/cedarbench_qwen35b_runH` |
| runI | `cedarforge/src/runs/repair_loop/cedarbench_qwen35b_runI` |

### Overall Results

| Method | Tasks | Passed | Pass rate | Avg semantic acc | Avg runtime |
|---|---:|---:|---:|---:|---:|
| `qwen35b` repair (mi=5) | 120 | 76 | 63.3% | 0.756 | 29.8s |
| `qwen35B_runE` repair (mi=5) | 121 | 95 | 78.5% | 0.821 | 9.3s |
| **`qwen35B_runG` repair (mi=20)** | 121 | 100 | **82.6%** | **0.879** | 16.9s |
| **`qwen35B_runH` repair (mi=20)** | 121 | 100 | **82.6%** | 0.857 | 17.4s |
| **`qwen35B_runI` repair (mi=20)** | 121 | 101 | **83.5%** | **0.881** | 16.4s |

runI achieves the highest pass rate (83.5%) and semantic accuracy (0.881). runG and runH tie at 82.6%.

### Stop Reason Distribution

| Stop reason | runG | runH | runI |
|---|---:|---:|---:|
| `verification_pass` | 100 | 100 | 101 |
| `oscillation_no_progress` | 19 | 20 | 19 |
| `max_iterations_reached` | 2 | 1 | 1 |

Almost all failures stopped due to oscillation, not from running out of iterations. This means additional iterations beyond 20 would not help the stuck tasks — they are structurally stuck.

### Final Failure Type Distribution

Failure layer of the last completed iteration for each failing task:

| Failure layer | baseline (mi=5) | runE (mi=5) | runG (mi=20) | runH (mi=20) | runI (mi=20) |
|---|---:|---:|---:|---:|---:|
| syntax | 24 | 8 | 9 | 10 | 10 |
| schema | 7 | 13 | 6 | 7 | 4 |
| semantic | 13 | 5 | 6 | 4 | 6 |
| **total failing** | **44** | **26** | **21** | **21** | **20** |

**Key observation:** Compared to runE, the G/H/I models significantly reduced schema failures (13→4–6). Syntax failures remain stubbornly at 8–10 across all fine-tuned models, pointing to a class of tasks where the model consistently produces malformed Cedar regardless of repair feedback.

### First Success Iteration — Window Breakdown

| Iteration window | runG | runH | runI |
|---|---:|---:|---:|
| iter 1–5 | 95 | 99 | 97 |
| iter 6–10 | 4 | 1 | 3 |
| iter 11–15 | 1 | 0 | 1 |
| iter 16–20 | 0 | 0 | 0 |
| never | 21 | 21 | 20 |

The vast majority of passing tasks succeed within the first 5 iterations. Iterations 6–20 rescued only 1–5 additional tasks. This suggests the benefit of extending `max_iterations` from 5 to 20 is marginal on its own — the main gains came from the stronger model and multi-turn context.

### Task-Level Transitions: runE → runI

| Outcome | Task count |
|---|---:|
| Fail → Pass (new wins) | 13 |
| Pass → Pass | 88 |
| Pass → Fail (regressions) | 7 |
| Fail → Fail | 13 |

**New wins (runE fail → runI pass, 13 tasks):**
`clinical_add_sponsor`, `hotel_add_cancel`, `hotel_add_franchise`, `hotel_add_renovation_lock`, `hotel_franchise_loyalty`, `hotel_remove_hierarchy`, `sales_add_regional_manager`, `streaming_add_download`, `streaming_add_trial_tier`, `streaming_remove_oscars`, `subscription_content_gate`, `tags_base`, `tags_sensitivity_and_owner`

**Regressions (runE pass → runI fail, 7 tasks):**
`data_lineage_ancestry`, `doccloud_graduated_sharing`, `sales_add_delete`, `sales_add_team`, `sales_full_expansion`, `streaming_add_geo_restriction`, `streaming_parental_controls`

Net gain: +6 tasks. The regressions cluster in `sales_*` and `streaming_*` scenarios, both of which involve complex multi-action schemas where the model now overshoots or misses optional-attribute guards.

### Tasks Failing in All Four Fine-Tuned Models (10 tasks)

These tasks fail across runE, runG, runH, and runI:

| Task | Final failure layer | Pattern |
|---|---|---|
| `hotel_add_loyalty_tier` | schema | Hallucinated attribute loop |
| `policy_annotations` | syntax | `@id(...)` placed after `}` — model never learns correct pre-permit placement |
| `sales_add_archive` | semantic | `floor_view_archived` floor not satisfied; model drops archive viewer permit |
| `streaming_full_expansion` | semantic | Two ceiling checks unresolved; complex datetime/duration conditions |
| `tags_add_approval` | syntax | Incomplete expression — `principal.allowedTagsForRole` truncated; also `<cedar_policy>` leakage |
| `tags_add_fourth_dimension` | syntax | Tags schema requires 4-dimensional role intersection; model loops on syntax |
| `tags_add_owner_bypass` | syntax | Same tags syntax oscillation pattern |
| `tags_add_role_c` | syntax | Same |
| `tags_add_sensitivity` | syntax | Same |
| `tax_base` | syntax | Complex tax schema; model consistently produces malformed output |

### Concrete Stuck Error Patterns

#### Syntax pattern 1: `<cedar_policy>` tag leakage

The model outputs `<cedar_policy>` as the first token of the policy body rather than stripping it. Cedar's parser rejects this immediately:

```
× unexpected token `<`
  ╭─[1:1]
1 │ <cedar_policy>
  · ┬
  · ╰── expected `@` or identifier
```

Occurs in `tags_add_approval`. The model was trained on the tagged format and sometimes emits the opening tag verbatim inside the policy.

#### Syntax pattern 2: annotation placement

The model places `@id(...)` annotations *after* the closing `}` of a policy instead of *before* the `permit`/`forbid` keyword:

```cedar
// Generated (wrong):
permit ( ... ) when { ... }
@id("viewer-read-published")    ← Cedar rejects: unexpected token @

// Correct:
@id("viewer-read-published")
permit ( ... ) when { ... }
```

Occurs persistently in `policy_annotations` across all four fine-tuned models despite repair feedback.

#### Schema pattern: hallucinated attribute (`hotel_add_loyalty_tier`)

The model cycles through non-existent attribute names on `Hotel`:

```
iter 1: resource.property.viewPermissions   ← "property" not found
iter 2: resource.viewPermissions.property   ← "viewPermissions" not found
iter 3: resource.property.viewPermissions   ← repeats
```

The repair feedback correctly identifies the wrong attribute each iteration, but the model substitutes a different hallucinated name rather than consulting the schema.

#### Schema pattern: missing `has` guard on optional attribute

Cedar requires `context has targetUser` before accessing `context.targetUser` when `targetUser` is declared optional (`?`) in the schema. The model consistently omits this guard in `sales_add_team` and `streaming_add_geo_restriction`:

```cedar
// Wrong — accesses optional attribute without guard:
when { context.targetUser.role == "distributor" }

// Correct:
when { context has targetUser && context.targetUser.role == "distributor" }
```

The schema validation error clearly states the issue each iteration, but the model does not reliably apply the `has` guard pattern.

#### Semantic pattern: floor not satisfied (`sales_add_archive`)

`floor_view_archived` requires that viewers can always view archived presentations. The model generates a policy that blocks archive access under certain conditions, and despite being shown the counterexample and the floor reference policy every iteration, it fails to relax the condition correctly.

#### Semantic pattern: complex ceiling check (`streaming_full_expansion`)

Two ceiling checks remain unresolved involving `datetime` + `duration` arithmetic:

- `subscriber_show_premium_or_not_early`: Subscriber may watch a Show only when `!isEarlyAccess OR tier==premium`
- `subscriber_must_watch_movie_no_rent_no_kid_in_region`: Non-kid in-region Subscriber must watch any non-rent movie

The counterexamples expose edge cases with extreme datetime values (e.g., `duration("-9223372036854775807ms")`), suggesting the model has difficulty reasoning about datetime boundary conditions in Cedar.

### Iteration Distribution

| Completed iterations | runG | runH | runI |
|---|---:|---:|---:|
| 1 | 59 | 61 | 55 |
| 2 | 26 | 23 | 29 |
| 3 | 6 | 7 | 9 |
| 4 | 3 | 5 | 3 |
| 5 | 1 | 3 | 1 |
| 6–7 | 2 | 1 | 2 |
| 8–9 | 16 | 12 | 15 |
| 10–15 | 6 | 8 | 5 |
| 16–20 | 2 | 1 | 2 |

The bimodal distribution (most tasks finish in 1–4 iters; a cluster finishes at 8–9) reflects the oscillation threshold: tasks that do not converge early tend to hit the oscillation detector at iteration 8 (threshold=6, starting from iteration 2 repairs).

### Updated Full Comparison Table

| Method | Tasks | Pass | Pass rate | Avg sem acc | Avg runtime |
|---|---:|---:|---:|---:|---:|
| `qwen35b` no repair | 121 | 59 | 48.8% | 0.607 | 10.8s |
| `qwen35b` repair (mi=5) | 120 | 76 | 63.3% | 0.756 | 29.8s |
| `qwen35B_runE` no repair | 121 | 51 | 42.1% | 0.625 | 6.1s |
| `qwen35B_runE` repair (mi=5) | 121 | 95 | 78.5% | 0.821 | 9.3s |
| `qwen35B_runG` repair (mi=20) | 121 | 100 | 82.6% | 0.879 | 16.9s |
| `qwen35B_runH` repair (mi=20) | 121 | 100 | 82.6% | 0.857 | 17.4s |
| **`qwen35B_runI` repair (mi=20)** | **121** | **101** | **83.5%** | **0.881** | **16.4s** |

### Open Questions

1. **Syntax oscillation on `tags_*`:** The model cycles through malformed tag-access expressions without converging. May require targeted training examples showing correct `has`-guarded tag policy patterns.

2. **Annotation placement (`policy_annotations`):** The `@id(...)` pre-permit placement is a recurring failure. A single training example that gets this right may fix it.

3. **Regressions in `sales_*` and `streaming_*`:** 7 tasks regressed from runE. Worth investigating whether a lower learning rate (runH) or a different checkpoint resolves these without losing the 13 new wins.

4. **Multi-turn vs single-turn contribution:** The improvement from runE (mi=5, single-turn) to runG/H/I (mi=20, multi-turn) conflates model quality improvement with repair loop upgrade. A controlled comparison (runG with mi=5 single-turn) would isolate the repair loop contribution.

## Data Source

The numbers in this document were derived from per-task `summary.json` files under:

- `cedarforge/src/runs/no_repair_loop/cedarbench_single_qwen35b`
- `cedarforge/src/runs/repair_loop/cedarbench_repair_qwen35b`
- `cedarforge/src/runs/no_repair_loop/cedarbench_repair_qwen35b_runE`
- `cedarforge/src/runs/repair_loop/cedarbench_repair_qwen35b_runE`
- `cedarforge/src/runs/repair_loop/cedarbench_qwen35b_runG`
- `cedarforge/src/runs/repair_loop/cedarbench_qwen35b_runH`
- `cedarforge/src/runs/repair_loop/cedarbench_qwen35b_runI`
