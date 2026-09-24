# Hinglish Code-Switched TTS — Initial Plan (v0, 2026-09-23)

> Original brainstorm as pasted at project start. Superseded by 01_research_proposal.md.

## 1. The idea, in plain language

Build a text-to-speech (TTS) model that speaks natural Hinglish — mixing
Hindi and English in one sentence the way real bilingual Indians actually
talk — and specifically make it sound *smooth* at the exact moment the
language switches, which is where every existing system currently breaks
down or sounds robotic.

Goal: a research paper, with a working prototype/demo if time and compute
allow.

## 2. Problem statement

Existing Hinglish TTS systems can produce intelligible mixed-language
speech, but none of them have been rigorously fine-tuned on real,
spontaneous code-switched speech, and none of them measure naturalness
specifically at the language-switch point.

## 3. Prior work noted at v0

- harrrshall/hinglish-tts: IndicF5 + IndicXlit + duration patch; 4.70/5 intelligibility
  on 30 scripted sentences via 3-ASR consensus; zero fine-tuning; no naturalness number.
- Dhoundiyal et al. (2023), Tacotron-based Hinglish TTS with phrase-break multi-task.
- HiACC (Singh, Singh & Kadyan 2025), 5.24 h, Zenodo 15551669.
- HingCoS, MSR Hindi-English corpus, Phonetically Balanced Hindi-English corpus.

## 4. Novelty claim at v0

1. Fine-tune on real spontaneous code-switched speech.
2. Switch-point-specific evaluation (Switch Discontinuity Score, SDS).

## 5. SDS sketch at v0

Tag switch points; extract F0 / duration / energy / MFCC discontinuity in a
200–300 ms window; compare against non-switch word boundaries; validate against
bilingual human ratings of the switch moment only.

## 6. Phases at v0

Baseline → data prep → fine-tune IndicF5 on HiACC → evaluate → ablation → write-up → demo.

## 7. Open questions at v0

Dhoundiyal overlap; child speech; forced alignment; compute; raters; licenses; test set.
