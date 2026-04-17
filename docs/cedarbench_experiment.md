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
