# CP@1 40-task panel — analysis

**Panel:** `CP40-V6`; 20 HumanEval+ unused + 20 MBPP+ unused.
**Panel SHA-256:** `14161ce8121aa9b75dafb7af443976ff0db233a88e70f22a2789b9ba53df8ffe`.
**Invalid:** False (missing anchor=0, complement=0; status anchor={'fail': 22, 'pass': 17, 'timeout': 1}, complement={'fail': 25, 'pass': 15}).

| Group | n | Anchor | Complement | Union | Δ union−anchor | b | c | one-sided p | two-sided p | 95% gain CI | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| combined_40 | 40 | 17 | 15 | 18 | +1 | 1 | 0 | 0.5000 | 1.0000 | [0, 3] | INCONCLUSIVE |
| humaneval_20 | 20 | 8 | 6 | 9 | +1 | 1 | 0 | 0.5000 | 1.0000 | [0, 3] | INCONCLUSIVE |
| mbpp_20 | 20 | 9 | 9 | 9 | +0 | 0 | 0 | 1.0000 | 1.0000 | [0, 0] | FAILURE |

**CP@1:** raw pair union 0.45; global-adjusted 0.419895; nine-config sensitivity 0.418995.

**Pre-registered rule:** success if combined union − anchor ≥ +4/40 and exact one-sided McNemar p<0.10, or the 95% paired-bootstrap CI lower bound >0; failure if union ≤ anchor; otherwise inconclusive. +2/40 (p=0.25) and +3/40 (p=0.125) are a practical floor, not significance; +2/40 all-win is inconclusive. HumanEval and MBPP subgroups are descriptive, not decision-bearing.

**Power caveat:** The 14x60 expected gain is +5/60 = +3.3/40; the 40-task exact McNemar is a screen, not a powered confirmation. The panel is a real-code-benchmark transfer test.

**Note:** because the union contains the anchor, `c` (anchor-only passes) is 0 by construction; the test is equivalent to a one-sided sign test on the complement-only passes.
