# 13 — SwitchMOS: the language-independent, switch-aware naturalness predictor

**Status:** adopted direction as of 2026-09-29. **Name:** "SwitchMOS" is a working name (decision D3). This file is the main specification; `../11_switch_aware_predictor.md` holds the evidence (novelty search, dataset counts).

## 13.1 What it is, in one paragraph

SwitchMOS is a learned naturalness predictor, like UTMOS. Give it a code-switched speech clip and its transcript, in any supported language pair, and it returns **one whole-clip naturalness score** plus **a score for every language switch** that explains it. It is trained on human pairwise preferences, and it looks at the switch points explicitly, because that is where code-switched TTS fails and where every existing predictor is blind.

## 13.2 How it relates to SDS

The project now has two layers.

| Layer | What it is | Learned from | Output | Role |
|---|---|---|---|---|
| **1. SDS switch diagnostics** (files 01–10 of this guide) | Hand-designed features at each switch, compared against natural speech | Natural code-switched speech (no ratings) | Per-switch percentiles, under/over-marked flags, seam probability, plain-language diagnosis | Interpretable features; input to layer 2; explanation of its scores |
| **2. SwitchMOS** (this file) | Neural predictor with a whole-clip branch and a switch branch | Human pairwise preferences | Whole-clip score + per-switch scores | The headline tool people will use |

Nothing in files 01–10 is wasted. Alignment, switch detection, features, controls, and the speaker-disjoint split all feed layer 2.

## 13.3 Why whole-clip + switches, not switches only

A clip can be natural at the switch and robotic everywhere else. A switch-only score would call it human. So the headline number covers the whole clip; the switch scores explain it and catch what whole-clip predictors miss.

## 13.4 Why language-independent

- SpeechArenaBench has pairwise human preferences for 10 Indian languages, and 78% of its sentences are code-mixed with English. That's ~10 language pairs in one format.
- SpeechJudge (ICLR 2026) has Mandarin–English code-switched preferences (data availability to be verified).
- Nothing in the architecture is Hindi-specific once the encoder, alignment, and switch detection are multilingual.

## 13.5 Architecture

```
audio + transcript (+ language-pair id)
 ├─ Multilingual SSL encoder (mHuBERT-147 / MMS-300M / w2v-BERT 2.0) → frame embeddings
 ├─ Whole-clip branch:  attention pooling over all frames → clip vector
 ├─ Switch branch:
 │    MMS + uroman alignment → word times
 │    switch detection: script change, or word-level language ID when scripts are shared / transliterated
 │    per switch: pooled embeddings in an asymmetric window + SDS features (pause, rate, lengthening,
 │                F0 jump/range/slope, energy jump, spectral jump)
 │    attention over switches → switch vector  (learned "no switch" vector if none)
 ├─ Language-pair embedding (lets "natural" differ by pair)
 └─ Heads:
      clip score            (main output)
      per-switch score      (explanation; weakly supervised)
      auxiliary: 6 SpeechArenaBench axes (noise, liveliness, voice quality, expressiveness, hallucinations, intelligibility)
      auxiliary: per-switch control class (natural / spliced / under / over)
```

## 13.6 Training data and labels

| Data | Labels | Used for |
|---|---|---|
| SpeechArenaBench, 10 languages | Pairwise preference (A > B, tie); 6 axis ratings per clip | Main training signal |
| SDS controls built from natural code-switched speech | Per-switch class, free | Pretraining the switch branch |
| SpeechJudge zh–en (if released) | Pairwise naturalness | Extra pair; or held out for zero-shot test |
| Our human study (Hinglish, switch-focused) | Switch ratings + clip MOS | **Test only** |

**Label caveats to resolve first:** some SpeechArenaBench preferences list two systems at once ("Gemini 2.5 Pro TTS, Eleven Labs v3"), and early axis ratings look nearly binary (1 or 5).

## 13.7 Training stages

1. **Switch-branch pretraining** on controls: classify each switch as natural / spliced / under-marked / over-marked.
2. **Preference training:** Bradley–Terry loss, P(A preferred) = σ(s_A − s_B); ties handled with a tie-aware variant; rater embedding as in UTMOS; auxiliary axis heads.
3. **Optional calibration** to a 1–5 scale on any absolute-MOS data.

Compute: a ~100–300M-parameter encoder fine-tuned with small batches fits one 16 GB A16; the 4×A16 server is enough.

## 13.8 How it's tested (the equivalent of test-set accuracy)

| Test | Split | Metric | Proves |
|---|---|---|---|
| **Held-out systems** | Train on some TTS systems, test on others | Pairwise accuracy; Kendall τ of system ranking vs human Bradley–Terry ranking | Doesn't just memorize systems |
| **Held-out languages** (leave-one-language-out, all 10) | Train on 9 pairs, test on the 10th | Same | **Language independence** |
| Cross-family (if data) | Train on Indic, test zero-shot on zh–en | Same | Generalization beyond Indic–English |
| **Switch-branch ablation** (headline) | Same model with vs without switch branch | Pairwise accuracy on code-mixed pairs; no loss on monolingual | Switch modelling matters |
| Baselines | UTMOS; SpeechJudge-GRM zero-shot; same encoder without switch branch; duration-only; SDS alone | Same | Beats what exists |
| Defect stratification | Pairs with vs without axis-rated defects | Same | Not only catching obvious noise/hallucination |
| **Switch-score validity** | Our Hinglish switch-focused human study | Correlation of per-switch scores with switch ratings | Per-switch scores mean something to listeners |
| Robustness | Loudness, sample rate, ±20 ms alignment jitter | Score stability | Usable in practice |

**When is it "a score"?** It beats the no-switch-branch model on code-mixed pairs, holds up on held-out systems and held-out languages, its per-switch scores correlate with the human switch ratings, and the model, code, and test results are public.

## 13.9 Output format

```json
{"clip": "utt_0042.wav", "language_pair": "hi-en",
 "switchmos": 3.62,
 "switches": [
   {"words": ["लिए", "late"], "time_s": 1.84, "score": 2.9,
    "sds": {"switch_pct": 91, "marking": "under", "seam_prob": 0.72},
    "diagnosis": "under-marked: no slowdown, flat pitch; seam likely"},
   {"words": ["late", "हो"], "time_s": 2.31, "score": 3.8, "sds": {"switch_pct": 48, "marking": "natural", "seam_prob": 0.08}}
 ]}
```

## 13.10 What is claimed

- Primary: a switch-aware naturalness predictor beats the same predictor without a switch branch on code-switched speech.
- Generalization: holds on held-out Indic–English pairs (leave-one-language-out).
- Not claimed: "first code-switched predictor" (SpeechJudge did Mandarin–English), or validity for pairs never tested.

## 13.11 Language-dependent pieces and how each is handled

| Piece | Handling |
|---|---|
| Encoder | Multilingual SSL model, chosen by a small pilot |
| Alignment | MMS + uroman (1,100+ languages) |
| Switch detection | Script change for distinct-script pairs; word-level language ID for shared-script pairs and transliterated English (known gap for v1) |
| What "natural" looks like | Language-pair embedding; SDS reference packs per pair where natural code-switched speech exists |
| Human validation of switch scores | Hinglish only in v1; other pairs stated as future work |
