# Behavioral Report Cards: 8 Bytes, 91 Answers, and the Boundary That Made Us Honest

**TL;DR.** Eight bytes can store the pass set of a 60-task coding benchmark. That buys exact pair and union queries, exact report cards, and 91 answers without model calls. It does not buy a selector: the exact header fails to transfer to a split, a new matrix, a new task set, or a second model family. This essay is the story of the build, the demo, the results, and the boundary—structured after real hackathon winner papers (see Structure notes).

## 1. The problem

We pick quantization configurations by weight error or perplexity, but deployment is judged by a different question: which tasks does this configuration actually pass? On a 14-configuration × 60-task matrix, the answer is 840 generations. The pass set itself is tiny—one bit per task. The waste is not storage; it is re-running everything to answer pair and union questions.

The prior study had already produced a split negative result. It motivated one missing primitive: a compact, auditable way to store the pass set without re-running every configuration. This essay is about that primitive and, more importantly, about the boundary we found while trying to turn it into a selector.

**Related work.** Prior aggregate evaluations (Li et al., ICML 2024, arXiv:2402.18158) guide quantizer choice by average performance and do not report per-configuration pass-set complementarity or the split-half/cross-matrix boundary. Natural-language report cards (Yang et al., 2024, arXiv:2409.00844) summarize behavior qualitatively; our unit is the exact per-task pass set with a transfer-boundary certificate. The distinction is the evidence unit and the certificate, not the label.

## 2. What we built

The primitive is a behavioral pass-set header: a bitset of 60 tasks in 8 bytes, 80 tasks in 10 bytes, one bit per task. The header is the pass set, so pair and union selection is exact **within the observed matrix**: 0.00 regret, 0.0000 union MAE, 1.00 top-3. The best pairs are 41/60 and 56/80.

On top of the bitset we built three things:

- a **report card** that answers all 91 pair/union queries for the 14×60 matrix from the stored 8-byte headers, without re-running the 14 configurations (840 generations), without model calls;
- a **certificate layer** (Rule CI, CP@1, exact-pair and cross-matrix certificates) that records what the header does and does not prove;
- a **public bundle**: manifest 17/17, staged bundle 79/79, SHA256SUMS, and the release repo `behavioral-report-cards`;
- a **750 MB Hugging Face candidate**: `AntonROSSO/qwen2.5-coder-1.5b-mx2-aq6-q3ks` (Apache-2.0; SHA256 `7fe6c14d…`).

The key demo number is not the exactness. It is the complement: a configuration that passes 31/60 alone contributes only **5** unique tasks outside the anchor, so the pair gain is 5, not 31. A standalone ranking overstates its contribution by 26 tasks.

## 3. The demo

The demo is one command, `report_card.py`, over the stored headers. It reconstructs every pair and union for the 14×60 matrix, prints the best pair, and shows the complement's true marginal contribution—no model call, no GPU, no 840 generations. The "wow" moment is the 31-versus-5 gap: the thing that looks like the best second configuration is mostly redundant once you can see the pass set.

We built the demo first and worked backward, the same discipline that won the MIT LLM Hackathon and the Climate Data Hackathon (see Structure notes). The exactness is the setup; the gap is the punchline.

## 4. How it works

For each configuration \(c\), the pass set \(P_c\) is the set of probes it passes under a fixed protocol. The probe passport records task ID, prompt hash, seed, runtime, result, and timestamp, so \(P_c\) is reproducible without the transcript. The header is the bitset of \(P_c\).

Because the header is the pass set, the oracle pair and union are available without prediction. The certificate layer binds the exactness (EXACT-HEADER-PAIR-01) and the boundary (EXACT-HEADER-CROSS-01), and CP@1 gives a false-pass-adjusted pass@1 point estimate (0.6376/0.6532; upper-false-pass sensitivity 0.612/0.627). Selection coverage—whether the selected pair is the true best—is reported separately, never as CP@1.

The header is 256×/204.8× smaller than MinHash-512 (14×60/12×80) and 8×/6.4× smaller than Bloom-512. MinHash matches the 14×60 selected-pair count, regret, and top-3 (12×80 top-3 0.9955, selection coverage 0.965) but not exactness (union MAE 0.0079), and costs 2,048 bytes.

## 5. The results

Within the observed matrix, the header is exact and cheap: 0.00 regret, 0.0000 MAE, 1.00 top-3, best pairs 41/60 and 56/80, 91 queries without model calls.

The boundary is the real result:

- **Split-half:** 1.91/1.70 regret, 3.00/3.47 MAE, 0.208/0.079 top-3; config stability 40.5%/41.1%. The out-of-sample bars are not met.
- **Cross-matrix:** 48/80 vs 56/80 and 34/60 vs 39/60 common-config; a KV8-inclusive 13×80 matrix adds **0** union.
- **CP40 panel:** anchor 17/40, complement 15/40, union 18/40 (+1), one-sided exact McNemar p=0.5, CI [0,3], **INCONCLUSIVE**; the MBPP subgroup is flat.
- **Gemma second family:** storage replicates exactly (5 B/40, 8 B/60; 0.00/0.00/1.00), but transfer does not replicate numerically (full-matrix best selected 0.572/0.507/0.276; selection coverage 0.176/0/0; CP@1 not computed; target-best 0/6).
- **External selectors:** within-sample the exact header is unbeatable; out of sample MinHash and random projection can beat it on some metrics; L1 is worse; **no selector transfers the target-best**.

The honest summary: the header is a storage and audit artifact. It is not a selector.

## 6. What didn't work (limitations)

The CP40 panel was the honest result: +1 task, one-sided p=0.5, overall INCONCLUSIVE, MBPP 0 gain (FAILURE). We report it as inconclusive, not as a win.

The second family failed numerically: Gemma stores exactly but does not transfer. The external selectors did not transfer the target-best. A candidate repository/agentic benchmark (REPO-COMP-40: 40 tasks, 2 configs, 80 agent runs, 3 B discovery/5 B full header) is designed and pre-registered, but **not run**—it needs an authorized scored run, and we do not report it as evidence.

A late review caught re-introduced CP@1/selection-coverage mislabels and a CP40 status contradiction. We fixed those: CP@1 is a point estimate; 0.612/0.627 is the upper-false-pass sensitivity, not a confidence bound, Gemma reports selection coverage only, Bloom-512 gets its CP@1, and CP40 is one-sided/INCONCLUSIVE everywhere.

## 7. Reproducibility

The public release is live at `https://github.com/antonrosso34-maker/behavioral-report-cards` (main (tag v12): data, evidence, paper, README, SHA256SUMS; no weights, raw completions, or personal data). The source repository is private/404: `https://github.com/antonrosso34-maker/LLM-intagration` (main `a3bb980`, branch `team/architect-predictor` `be038a5…`). The 750.3 MiB contender is on Hugging Face at `https://huggingface.co/AntonROSSO/qwen2.5-coder-1.5b-mx2-aq6-q3ks` (Apache-2.0; SHA256 `7fe6c14d…`). The release SHA256SUMS are the audit trail; the DOI is pending.

## 8. Takeaways

1. **Store the pass set, not the selector.** The bitset is the evidence; the selector is a claim the evidence does not support out of sample.
2. **Exactness is matrix-local.** The same header that is exact within a matrix is a poor selector on a split, a new matrix, a new task set, or a new family.
3. **The boundary is the contribution.** The negative transfer result is more valuable than a near-oracle claim we cannot defend.
4. **The demo is the discipline.** Building the report card first forced every architectural decision toward the one number that matters: the complement's true marginal contribution.

## 9. Team

This work was built by an 11-agent research team (variance, threshold, proxy gap, routing, power, failure modes, transfer, calibration, benchmark, literature, bridge) with a red-team reviewer and a lead. The public bundle is the team's audit trail.

## Sources

- MIT LLM Hackathon 1st place (Catalyze): https://samanvya.dev/blog/mit-llm-hackathon-first-place
- Strong Compute ARC AGI2 1st place (ClosedAI): https://words.strongcompute.com/p/how-closedai-won-strong-computes
- Kaggle solution write-up rubric: https://www.kaggle.com/solution-write-up-documentation
- def/acc Hackathon standard template: https://pys8vc40ox3z7qxp.public.blob.vercel-storage.com/files/321d77559ec31923-8-ee0b5b9f27eb-def_acc-Hackathon-Standard-submission-template-proj_chacha.ai.pdf
- Climate Data Hackathon 1st place (Nightwalkers): https://ai-mission.eu/blog/hackathon-3-nightwalkers/
- Text-to-Manim 1st place: https://words.strongcompute.com/p/text-to-manim-generating-visual-explanations

## Structure notes

This essay borrows the structure of real hackathon winner papers: the MIT LLM Hackathon 1st place write-up (architecture → demo-backward → result; https://samanvya.dev/blog/mit-llm-hackathon-first-place), the Strong Compute ARC AGI2 1st place write-up (what the benchmark is → approach → results; https://words.strongcompute.com/p/how-closedai-won-strong-computes), the Kaggle solution write-up rubric (context → overview → details → sources; https://www.kaggle.com/solution-write-up-documentation), the def/acc Hackathon standard template (abstract → hypothesis → architecture → development path → limitations), the Climate Data Hackathon 1st place write-up (strategy → results → takeaways; https://ai-mission.eu/blog/hackathon-3-nightwalkers/), and the Text-to-Manim 1st place write-up (introduction → problem → results; https://words.strongcompute.com/p/text-to-manim-generating-visual-explanations). This synthesis—hook/TL;DR, problem, approach, demo, results, what didn't work, reproducibility, takeaways, team—is the skeleton above. The six sources share problem → approach → results; the TL;DR, demo, team, and Sources sections are additions, not a claimed intersection.












