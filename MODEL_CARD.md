# Model Card — Gemma 4 E2B compressed checkpoints (Q3 PTQ and G-P1 QAT-derived)

## Summary

A 3.18× Q3 PTQ checkpoint and a 3.36× QAT-derived G-P1 checkpoint for local code assistance
on consumer hardware. The measured QAT-family frontier is Unsloth UD-Q4 (3.55×, 2,498.98 MiB);
our checkpoints are honest points, **not** state of the art. UD-Q2 collapses behaviorally.

- **Source:** `ggml-org/gemma-4-E2B-it-GGUF` BF16, 9,311,305,152 bytes.
- **Q3 checkpoint:** 2,927,720,288 bytes (2,792.09 MiB), SHA256
  `1448b0c3eec5d53c678a8d5325213697b9ef5f387c36336beb269af06ed5505d`.
- **Q3 recipe:** Q3_K_M base; `attn_q=Q5_K`, `attn_k=Q5_K`, `per_layer_token_embd=Q5_K`;
  71 tensor overrides; code imatrix (200×512, 275 entries).
- **Q3 size:** 5.0397 bits per parameter over 4,647,450,147 storage parameters; 3.1804×.
- **G-P1 (QAT-derived):** 2,769,013,120 bytes (2,640.74 MiB), 4.766 bpp, 3.36× vs BF16;
  requantized from official Google QAT Q4_0 (3,194.35 MiB) with Q3_K_M, attention Q5_K,
  per-layer Q4_K, down/output Q5_K, and gate/up Q4_K on 20 layers.
- **Frontier reference (third-party):** Unsloth UD-Q4_K_XL, 2,620,370,976 bytes
  (2,498.98 MiB), 4.5293 bpp, 3.55×; UD-Q2_K_XL, 2,186,186,784 bytes (2,084.91 MiB), 3.7782 bpp,
  4.26×, rejected on behavior.
- **License:** Gemma 4 is Apache-2.0; these quantized checkpoints are derivatives and retain
  the Gemma 4 license and attribution.

## Architecture

`gemma4`, 35 blocks, hidden 1536, 8 heads / 1 KV head, vocabulary 262,144, 601 tensors.
The 2.35B-parameter per-layer token embedding is 50.5% of storage and is kept at Q5_K;
the default Q6_K rule would make the checkpoint 3,074.5 MiB (2.88×) and fail the 3× gate.

## Measured behavior

Settings: llama.cpp b12128 Vulkan, full offload, 6 threads, context 2048, f16 KV cache,
temperature 0, 30 s tests, max 512 tokens, reasoning off. MBPP-HO is the repaired 60-task
heldout; no BF16 behavior reference exists.

| Model | Size (MiB) | PPL | HE dev | HE held | MBPP-HO |
|---|---:|---:|---:|---:|---:|
| Q3 mix (ours) | 2,792.09 | 208.52 | 25/40 | 35/60 | 30/60 |
| Google QAT Q4_0 | 3,194.35 | 51.92 | 29/40 | 34/60 | 35/60 |
| G-P1 (ours) | 2,640.74 | 51.03 | 29/40 | 34/60 | 32/60 |
| Unsloth UD-Q4_K_XL | 2,498.98 | 47.15 | 29/40 | 36/60 | 35/60 |
| Unsloth UD-Q2_K_XL | 2,084.91 | 89.16 | 15/40 | 17/60 | 21/60 |

G-P1 is 17.3% smaller than QAT with equal dev/heldout, −3 MBPP-HO, and better PPL; it is
dominated by UD-Q4 (141.8 MiB larger, −2 heldout, −3 MBPP-HO, worse PPL). The Q3 mix keeps
a 1-task heldout edge over G-P1 but has PPL 208.52. Hit512 counts are 11/17/7; scores are
lower bounds for a longer completion budget.

## Hardware

Tested on an 8 GB AMD RX 6600 XT (Vulkan, full offload, 2k context). No peak-VRAM
minimum was measured; the 8 GB card ran the 2,499–2,792 MiB (2.440–2.727 GiB) checkpoints.
BF16 behavior was not measured under this protocol; CPU-only inference is possible with
16 GB RAM.

## Intended use

Local code assistance, offline experimentation, and compression research. Not intended for
safety-critical code execution, autonomous repository edits without review, or as a
replacement for frontier coding agents.

## Limitations

- Reasoning is disabled; Gemma 4 thinking mode produced empty completions at 512 tokens.
- G-P1/Q3 are non-SOTA; UD-Q4 is the measured frontier. UD-Q4/Q2 are third-party QAT quants.
- BF16 behavior was not measured under the chosen protocol; CPU/partial offload remains
  possible. BF16 PPL is a 20-chunk CPU subset, not comparable with full PPL.
- Private sealed set: 4/30 for the Qwen finalist; the Gemma private result is not claimed.
- Official Google QAT Q4_0 is measured; W4A16, AWQ, and GPTQ remain unmeasured.
- Data/license status is not a blanket redistribution claim.
- Evaluation is code-centric; SWE tasks are future work.
- Public release: https://github.com/antonrosso34-maker/behavioral-report-cards (tag v12).

## Provenance and license

The quantized weights are derivatives of Gemma 4 E2B (Google DeepMind, Apache-2.0).
llama.cpp is MIT. Redistribution must retain the upstream notices in `NOTICE`.

