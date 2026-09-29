# 05 — Architecture

**Recommended design: a gated set of experts (SwitchMoE), whose switch expert is trained on minimal pairs (SwitchEdit) and receives a label-free switch-likelihood signal (SwitchLM).**

## 5.1 Shared backbone

- **Multilingual self-supervised speech encoder** (mHuBERT-147 or XLS-R; WavLM is English-centric). Mostly frozen; features precomputed to save A16 time.
- **Learned layer weights** over encoder layers (the largest single effect in DAMOS's ablations).
- **Alignment and switch detection** from 04.

## 5.2 Experts

| Expert | Looks at | Inputs | Output |
|---|---|---|---|
| **Global** | Whole clip | Encoder frames → frame scores → late pooling | Clip-level naturalness |
| **Switch** | ±0.5–1 s window around each switch, encoded separately (so a defect elsewhere doesn't leak in) | Window embeddings + switch features (04) + SwitchLM surprisal | Score per switch |
| **Artefact** (optional) | Spectrogram | Small CNN (EfficientNet-B0), as in UTMOSv2 | Glitch / noise evidence |

## 5.3 Gate and combination

- A small gate decides how much each expert counts, conditioned on: number and density of switches, language pair, and a domain embedding.
- Clip score = gated mix of experts, **plus a soft-minimum over switch scores**, so one bad switch can pull the score down, as it does for listeners.
- Clips with no switches rely on the global and artefact experts.

## 5.4 Conditioning embeddings (UTMOS's most effective idea)

- **Rater** embedding during training (averaged at inference).
- **Language pair** embedding (what "natural" means can differ by pair).
- **Domain** embedding (dataset / system family).

## 5.5 SwitchLM (label-free feature)

- A small Transformer (20–50M) over word-level prosody tokens (pitch statistics, duration, energy, pause, pooled accent features), conditioned on words, language tags, and left context.
- Trained only on natural code-switched speech (03 §3.3).
- Its **surprisal** at each switch (how unexpected the switch sounds) is a feature for the switch expert.
- Not a standalone metric: the closest published analogue (TTScore-pro) correlates with humans at only ~0.05.

## 5.6 Heads

- Clip score (main output).
- Per-switch score.
- Auxiliary: the 6 SpeechArenaBench axes; per-switch control class (natural / spliced / under / over).

## 5.7 Size

Encoder ~95–300M (mostly frozen) + a few million trainable parameters in experts, gate, and heads. 25–100× smaller than SpeechJudge.
