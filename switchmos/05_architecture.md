# 05 — Architecture (v1)

Built from what published ablations show matters (see `02_related_work_and_novelty.md` §2.4), plus one new component.

```
audio (+ transcript, language pair, dataset id, rater id)
 ├─ Semantic branch   multilingual SSL encoder (w2v-BERT 2.0 / mHuBERT-147 / XLS-R; pilot)
 │                    learned layer weights → frame features → attention pooling
 ├─ Acoustic branch   mel-spectrogram CNN (EfficientNet-B0 class) → pooled features
 ├─ Local-event branch (new)
 │     MMS + uroman alignment → language switches (later: names, numbers, chunk joins)
 │     per event: SSL window features + switch features (04) + SwitchLM surprisal
 │     attention + soft-min over events; learned "no events" vector if none
 ├─ Conditioning      dataset/domain embedding (+ per-dataset score bias), rater embedding
 │                    (averaged at inference), language-pair embedding
 └─ Heads
       absolute MOS            clipped MSE, per-dataset bias
       pairwise preference     Bradley–Terry + Davidson ties; strength-aware for A+1 / A+2 labels
       6 SpeechArenaBench axes auxiliary
       per-event scores        explanation output
```

## Why each part

| Part | Why |
|---|---|
| Multilingual SSL encoder | English-trained encoders (WavLM) transfer poorly; SSL models generalize across languages better than codecs |
| Learned layer weights | Early layers carry synthesis quality, later layers intelligibility; biggest single ablation effect in DAMOS |
| Spectrogram branch | UTMOSv2: spectrogram best for absolute score, SSL best for ranking, fusion beats both |
| Local-event branch | Whole-clip pooling averages away brief problems; switches are where code-switched TTS fails |
| Dataset / domain bias | Different datasets use different scales (MOS, MUSHRA, pairwise); lets them train together |
| Rater embedding | Largest single effect in UTMOS |
| Bradley–Terry + ties | Beats regression on preference data; ties used, not discarded |
| Soft-min over events | One bad moment lowers perceived naturalness more than an average suggests |

## Size and compute

Encoder ~300–600M (mostly frozen, top layers fine-tuned) + a few million new parameters. Fits 16 GB A16s with cached features. 10–25× smaller than SpeechJudge's 7B.

## Later options (only if v1 leaves headroom)

- kNN retrieval head (VoiceMOS 2024 winner).
- Distillation: pseudo-label unlabelled modern TTS audio with SpeechJudge-GRM.
- Small audio-LLM judge as a comparison point.

## What we took from UTMOS and UTMOSv2 (their own ablations)

| Component | Effect | Taken? |
|---|---|---|
| Frame-level scores averaged to a clip score | Beat pooled training | Yes, but frame scores from a full-context encoder are not truly local (Kuhlmann 2025), so local scores come from switch-anchored windows |
| Contrastive / ranking loss | Works even without regression | Yes, as Bradley–Terry |
| Listener / domain embedding | Largest single effect in UTMOS | Yes |
| Multi-stage training | Largest effect in UTMOSv2 | Yes |
| Diverse modern training data | Crucial in both | Yes, and much broader |
| Spectrogram branch | Best absolute score | Yes |
| Multi-level stacking | +0.006 correlation | No |
| Phoneme encoder | Hurt on large data | No |

## Options considered for the local branch, and why this combination

| Option | Idea | Verdict |
|---|---|---|
| Label-free switch model alone (SwitchLM) | Surprisal of a switch under a model of natural speech | Too weak alone (TTScore-pro evidence); kept as a feature |
| Gated experts | Separate global / switch / artefact experts with a gate | Folded into the branch-and-fusion design |
| Minimal pairs (SwitchEdit) | Regenerate only a switch; learn "original is better" | **Main supervision for the local branch**: no prior quality predictor uses it, and it gives exact locations for free |
| Generic defect localizer (DAMOS-style) | Detect any distortion, gate it into the score | Gains were tiny; we anchor on linguistic events instead |
