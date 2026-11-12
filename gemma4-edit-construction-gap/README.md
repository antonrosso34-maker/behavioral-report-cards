# Patch Applicability in a Local 4-Bit Gemma 4 Agent: A Two-Split Audit

**Applicability is not correctness**

This is the public artifact release for the Gemma 4 Developer Agent Paper Track submission. The paper itself is submitted as a Kaggle Writeup; this release contains the audit harness, frozen splits, aggregate results, and saved model replies for verifiability.

- **Figure:** [figures/fig1_applicability_semantic.png](figures/fig1_applicability_semantic.png)
- **Frozen split:** [harness/split_20.json](harness/split_20.json)
- **Fresh split:** [harness/split_fresh_20.json](harness/split_fresh_20.json)
- **License:** Apache-2.0 for code; CC BY 4.0 for the paper and data. See [LICENSE](LICENSE) and [LICENSE-PAPER](LICENSE-PAPER).

## Key results

| Arm | Strict apply | Lenient apply | Test-verified semantic |
|---|---:|---:|---:|
| Gemma 4 E2B 4-bit, single-shot | 0/20 | 0/20 | 0/20 |
| Gemma 4 E2B 4-bit, retrieval + 1 repair | 6/20 | 10/20 | 0/20 |
| Gemma 4 E2B 4-bit, oracle file | 3/8 first-turn | 7/8 | 0/8 |
| Qwen2.5-Coder-14B 4-bit, oracle file | 3/20 | 6/20 | **1/20** (seaborn-3010) |
| Qwen2.5-Coder-32B 4-bit, oracle file | 0/20 | 1/20 | 0/20 |
| Qwen2.5-Coder-14B 4-bit, search/replace | 1/20 | 0/20 | 0/20 |

*S/R: 1/20 strict (`matplotlib-23563`, environment-limited), 0/20 lenient; 19/20 blocks rejected as `edit_not_found` or no-op.*
| Qwen2.5-Coder-14B 4-bit, fresh split | 1/20 | 3/20 | 0/20 |
| Qwen2.5-Coder-7B, 300-example QLoRA | 3/20 | 3/20 | 0/20 |

The frozen-split retrieval gain (0/20 → 6/20 strict, p=0.031) did not replicate on a fresh 20-task split (0/20 strict). The six strict applies are 0 verified passes, 1 tested failure, and 5 strict applies without a test verdict. The only test-verified semantic pass is a 14B Qwen comparison case for `mwaskom__seaborn-3010`; it is one cross-family anecdote, not a scale result.

## What is included

The paper is submitted as a Kaggle Writeup; its full text is not in this release. The artifacts below support verifiability.

- `harness/` — single-shot and retrieval runners, oracle runner, scorer, and the frozen/fresh split files.
- `results/` — aggregate audits for the 2.3B arms, the 14B/32B/S/R/fresh/QLoRA controls, and the oracle/fresh splits.
- `replies/` — saved model replies for the 14B, 14B fresh, 7B QLoRA, and 2.3B oracle arms. No hidden tests or gold patches are included.
- `figures/` — the applicability-vs-correctness figure.

## Reproduction

The paper was produced with llama.cpp (Vulkan) on an AMD RX 6600 XT 8 GB for the 2.3B arms, and Kaggle T4 GPUs for the Qwen 14B/32B and QLoRA controls. The harness scripts are self-contained; the splits pin the task IDs and base commits. See the paper's Method and Data availability sections for the exact prompts, scoring rules, and exclusions.

## Exclusions

No model weights, raw hidden-test content, gold patches, repository snapshots, or private data are included. The saved replies are model outputs only. The hidden-test logs are not included; the paper reports only aggregate outcomes and the valid `seaborn-3010` control.

## Citation

Anton Rosso, “The Edit-Construction Gap: One 14B Success and the 2.3B Floor,” Gemma 4 Developer Agent Paper Track, 2026.
