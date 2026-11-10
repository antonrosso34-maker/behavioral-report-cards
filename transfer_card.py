#!/usr/bin/env python3
"""Cross-family transfer card: a graded difficulty prior, not a selector.

Existing-evidence analysis only: no model, GPU, or network. Reports the
Qwen-vs-Gemma pass-rate association, decile/quartile overlap, and the
selection boundary that makes the card a prior rather than a top-k list.
"""
from __future__ import annotations

CARD = {
    "association": {"spearman_qwen_gemma": 0.6215, "n_tasks": 100},
    "hard_decile": {"qwen_mean_pass": 0.283, "gemma_easy_decile_pass": 0.800},
    "hard_decile_overlap": {"same_tasks": "5/10", "bootstrap": "0.426 [0.2, 0.7]"},
    "hard_quartile": "12/25",
    "easy_decile": "4/10",
    "boundary": {
        "within_family_llama": "12/12",
        "update_qadapter_gemma": "0/10",
        "split_half_reversal": "12/60",
        "storage": "exact",
        "selection": "not transferable",
    },
}


def main() -> None:
    c = CARD
    print("transfer card (graded difficulty prior; not a top-k selector):")
    print(f"  Qwen-vs-Gemma pass-rate Spearman: {c['association']['spearman_qwen_gemma']} (n={c['association']['n_tasks']})")
    print(f"  hard decile: Qwen mean pass {c['hard_decile']['qwen_mean_pass']} vs Gemma easy-decile {c['hard_decile']['gemma_easy_decile_pass']}")
    print(f"  same hard tasks across families: {c['hard_decile_overlap']['same_tasks']} (bootstrap {c['hard_decile_overlap']['bootstrap']})")
    print(f"  hard quartile overlap {c['hard_quartile']}; easy decile overlap {c['easy_decile']}")
    print(f"  boundary: within-family {c['boundary']['within_family_llama']}, update/Q-Adapter/Gemma {c['boundary']['update_qadapter_gemma']}, split-half reversal {c['boundary']['split_half_reversal']}")
    print("claim: prioritize hard tasks, but do not expect the same ten tasks; the card is a prior, not a selector.")


if __name__ == "__main__":
    main()
