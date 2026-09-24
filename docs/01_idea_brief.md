# 01 — Idea Brief (v1, 2026-09-23)

## One sentence

Code-switched TTS is evaluated on whole sentences, but its characteristic failure lives in the ~300 ms where the language changes; we propose a switch-localized metric calibrated to how real Hindi-English bilinguals actually switch, validate it against switch-only human judgments, and use it to show what fine-tuning on spontaneous Hinglish does and does not fix.

## The problem

Say "मुझे office के लिए late हो गया" to any Hindi-capable TTS. The words are usually intelligible. What sounds wrong is the seam: a flat or abrupt transition into "office", a rushed "late", a pitch reset that no human would produce. Every existing evaluation (MOS, CMOS, CER, speaker similarity, UTMOS) scores the whole utterance and averages this moment away. AI4Bharat's 120,000-rating Hinglish benchmark, IndicF5's own 30-sentence code-mix test, and the harrrshall/hinglish-tts intelligibility score all share this blind spot.

## The insight that makes this a research question

The v0 assumption was "less discontinuity at the switch = more natural". The phonetics literature says that is wrong. Bilinguals slow down before a switch, raise pitch and lengthen the switched word, and in Hinglish specifically speak the embedded English slower and louder than the surrounding Hindi (Rao et al., IIT-B, Interspeech 2018). Listeners use these cues, and splicing them out measurably hurts comprehension (Shen et al. 2020). So a good code-switched TTS must *reproduce the human switch signature*, not erase it. That reframes the metric from "join cost" into a hypothesis test.

## Contributions (in priority order)

1. **Switch Discontinuity Score (SDS).** A reference-free acoustic metric computed in an asymmetric window around each language switch: rate, duration, F0, energy, and spectral contrast, normalized against non-switch word boundaries in the same utterance, and scored as distance from the empirical distribution of natural Hinglish switches. Two terms: *seam* (splice-like artifacts, never natural) and *prosody* (under- or over-marking relative to humans).
2. **A switch-window human rating set.** ≥500 excerpts across natural speech, spliced controls, and 6–8 TTS systems (open and closed), rated for switch naturalness only, plus a behavioural word-identification task. Released with the code. Shows the local–global dissociation: systems that tie on utterance MOS separate at the switch.
3. **A Hinglish case study.** Fine-tune IndicF5 (336 M, flow matching) on HiACC, the only open spontaneous Hinglish corpus with token-level switch labels (3.22 h adult). Report SDS, monolingual-quality retention, and ablations over data type (spontaneous vs read vs synthetic), script policy (Devanagari vs Latin English), and adaptation method (LoRA vs full). Expected honest result: spontaneous data moves the prosody term toward human, at some cost in signal quality.
4. **Side finding.** F5-family models allocate output duration by UTF-8 byte count, which misallocates time inside mixed-script sentences even after the known whole-sentence patch. Quantified per switched word.

## What is and is not novel

- Fine-tuning a TTS on spontaneous code-switched speech: **already done** for Mandarin-English (SEAME → CosyVoice2, 2025–26) and, without a paper, for Hinglish (Orato, 194 h). We do not claim "first". We claim the first *measured* one.
- A switch-localized, human-calibrated acoustic metric: **not done** in any language pair. Three 2026 papers circle it (LCG evaluates the embedded phrase locally; MagpieTTS-LF measures F0/energy jumps at chunk boundaries; Yeo et al. use a frame-level code-mixing index) without closing it.
- Hindi-English acoustic switch distribution on spontaneous speech: **not done** since Rao 2018, which used rehearsed public speech.

## Why it matters

~250 M Indians code-switch daily. Sarvam, Gnani, and Gradium all market smooth mid-sentence switching and none has a metric for it. CS-ASR augmentation papers synthesize Hinglish and cannot check whether the switches are realistic. CALCS 2025 had no TTS papers at all.

## Deliverables

- Paper (Interspeech-shape, 4 pages + refs).
- `sds/` Python package: alignment (MMS + uroman), features, reference distributions, scoring.
- Rating set + protocol.
- Fine-tuned checkpoint + audio demo (baseline vs fine-tuned, same sentences).

## Feasibility in one line

HiACC is a 531 MB download under CC BY; IndicF5 ships its training stack; the whole compute budget is 50–100 GPU-hours on a single A100; 5–8 bilingual raters suffice for the correlation claims.

## Pointers

- 02_novelty_assessment.md — reviewer-eye verdict and threat table
- 03_prior_work_and_positioning.md — full literature, where we stand
- 04_switch_point_evaluation.md — SDS v1 definition, human protocol, tooling
- 05_datasets_and_licenses.md — HiACC and alternatives
- 06_base_models_and_finetuning.md — IndicF5, recipe, compute
- 07_importance_and_venues.md — evidence of importance, venues
- 08_research_plan_and_risks.md — phases, ablations, failure modes
