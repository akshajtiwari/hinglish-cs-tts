# 02 — Novelty and Importance Assessment

Adversarial review conducted 2026-09-23 (~45 searches, ~40 pages opened, arXiv + Semantic Scholar API sweeps). Written from the point of view of a skeptical Interspeech/ICASSP/ACL reviewer. See 03_prior_work_and_positioning.md for the full citation list.

## 2.1 Short verdict

| Contribution as originally framed | Verdict | One-line reason |
|---|---|---|
| (a) First fine-tune of a Hinglish TTS on real spontaneous code-switched speech | **Incremental / largely done** | Same recipe published for Mandarin-English (SEAME → CosyVoice2, 2025–26); Orato already fine-tuned IndicF5 on 194 h Hinglish call audio (no paper) |
| (b) Switch Discontinuity Score, a switch-localized, human-validated acoustic metric | **Novel as a package; each component has precedent** | No paper computes reference-free acoustic discontinuity at language switches, normalizes within-utterance, and validates against switch-only human ratings. But boundary F0/energy jumps (MagpieTTS-LF 2026), frame-level acoustic CS index (Yeo 2026), local phrase evaluation (LCG 2026), and 1990s–2000s join-cost work all exist |
| (c) Fine-tuned model beats strongest open baseline on (b) | **Incremental** | Standard demonstration; and "strongest open baseline" is contested by the AI4Bharat 120k-rating benchmark where IndicF5 is not top |
| Importance | **High practical, moderate academic** | ~250 M daily Hinglish code-switchers; industry (Sarvam, Gnani, Gradium) explicitly markets the switch moment yet has no metric for it; CALCS 2025 had zero TTS papers |

**Overall:** the idea is worth doing, but only if the paper is a **metric + validation-set paper** with the fine-tune as a case study, not a "we fine-tuned IndicF5" paper. Reframed that way it fills an open gap that three 2026 papers have circled without closing.

## 2.2 Closest prior work (threat table)

| # | Work | What it covers | Threat to (a) | Threat to (b) |
|---|---|---|---|---|
| 1 | Yeo et al., APSIPA 2025 — https://arxiv.org/abs/2601.00935 | CosyVoice2 fine-tuned on SEAME (spontaneous zh-en), up to 100 h; UTMOS only; fine-tune *lowers* UTMOS | **Full** for zh-en | none |
| 2 | Yeo et al., arXiv Jun 2026 — https://arxiv.org/html/2606.19381 | Adds CMI_speech: frame-level acoustic code-mixing index from ASR cross-attention, used as preference critic; needs ground truth; no human eval | Full for zh-en | **Partial**: acoustic, boundary-motivated, but measures language balance, not discontinuity; not reference-free |
| 3 | Lee et al., LCG, EMNLP 2026 — https://arxiv.org/html/2609.01016v1 | Argues global naturalness conflates dimensions; localized eval (Whisper-LID on embedded phrase, phrase-nativeness AB N=488); en/de/fr × ja/ko | none | **Partial**: the "evaluate the switch locally" framing is published; the acoustic-discontinuity instantiation is not |
| 4 | Ghosh et al., MagpieTTS-LF, Interspeech 2026 — https://arxiv.org/abs/2606.18485 | Prosodic Boundary Discontinuity: ΔF0, ΔEnergy in ±1000 ms at chunk boundaries; not human-validated; not language switches | none | **Partial**: boundary F0/energy jump on neural TTS exists |
| 5 | tryorato/orato-tts-hindi-v1 — https://huggingface.co/tryorato/orato-tts-hindi-v1 | IndicF5 fine-tuned on ~194 h Hindi/Hinglish call audio; CER + SpkSim only | **Partial**: "first Hinglish IndicF5 fine-tune" is dead | none |
| 6 | Zhang & Lin 2021 — https://arxiv.org/abs/2110.07210 | Found/low-quality real CS data to teach switching | Partial: precedent for "real not studio" | none |
| 7 | SwitchLingua, NeurIPS 2025 D&B — https://arxiv.org/html/2506.00087 | Utterance-level "switching naturalness" score (human + GPT-4o) | none | Partial by name only |
| 8 | Zuo et al., arXiv Sep 2026 — https://arxiv.org/abs/2609.11545 | "Duration abnormal rate" for CS inputs, utterance-level | none | Partial |
| 9 | Anand et al., Voice-First Nation, 2026 — https://arxiv.org/html/2604.21481v2 | 120k pairwise ratings, 4,164 code-mixed Hinglish sentences, 7 systems; Gemini > Bulbul > … > IndicF5 | none | Adjacent: proves raters exist; proves utterance-level rating is the norm; **contests baseline choice** |
| 10 | Join-cost literature (Hunt & Black 1996; Vepa & King 2006; Stylianou & Syrdal 2001) | Spectral/F0/energy discontinuity at joins, validated on listener join-ratings | none | **Ancestor**: reviewers will call SDS "join cost at switch points" |
| 11 | Negroni et al. 2024 — https://arxiv.org/abs/2408.13784 ; PartialSpoof — https://github.com/nii-yamagishilab/PartialSpoof | Splice-point discontinuity features alone reach 6% EER on partial-spoof detection | none | Supports SDS premise; also a competitor feature set |
| 12 | Kuhlmann et al., Interspeech 2025 — https://arxiv.org/abs/2508.10374 ; XSQ-AST 2026 — https://arxiv.org/abs/2609.24770 | Frame-level MOS; crowdsourced localization of artifacts | none | Template for switch-local human protocol |

Empty searches (evidence of gap): Semantic Scholar returns zero hits for "code-switch boundary naturalness text-to-speech", "switch point discontinuity synthesized speech", "prosodic discontinuity metric neural TTS boundary". No "boundary MOS" or switch-only rating protocol for CS-TTS found. No academic paper fine-tunes any TTS on HiACC. No CS-TTS section in the 2025 TTS survey (arXiv 2510.07037).

## 2.3 The scientific twist that makes (b) defensible

The v0 plan assumed *less* discontinuity at the switch = more natural. The phonetics literature says the opposite is closer to the truth:

- Bilinguals **slow down before a switch** and listeners use that cue (Fricke, Kroll & Dussias 2016, Bangor Miami corpus).
- The switched word gets **higher pitch, wider range, longer duration** (Olson 2012, 2016; Muldner et al. 2019; Wang, Xu & Franich 2026).
- **Hinglish specifically:** embedded English is slower, louder, with more pitch variation than surrounding Hindi (Rao et al., IIT-B, Interspeech 2018).
- Switches are preferentially placed at **intonation-unit boundaries** with legitimate pauses and F0 resets ("prosodic distancing", Torres Cacoullos 2020).
- **Splicing out these cues hurts comprehension** (Shen, Gahl & Johnson 2020) — which is exactly what a TTS that synthesizes each language independently does.

So the right formulation is **SDS = distance between the synthetic switch's feature vector and the empirical distribution of natural Hinglish switches**, with under-marking (robotic seam) and over-marking (exaggerated pause/reset) reported separately. Nobody in the threat table does this, and it turns a "join cost rebrand" into a hypothesis-driven metric: *good CS-TTS reproduces the human switch signature, it does not erase it.* That is the paper.

## 2.4 What reviewers will say, and the pre-emptive answer

| Objection | Answer built into the plan |
|---|---|
| "This is join cost with a new name" | Headline the within-utterance normalization, the natural-reference calibration, and the switch-only human validation; benchmark SDS against raw join cost, PBD (#4), CMI_speech (#2), LID confidence (#3), duration-abnormal rate (#8) on the same human ratings |
| "Fine-tuning on spontaneous CS is done (SEAME)" | Cite #1/#2/#5/#6 as precedent; reframe (a) as data-efficiency + style-transfer study: 3 h phone-mic vs read vs synthetic CS vs call-domain; LoRA vs full; monolingual-quality retention |
| "3 h of 16 kHz phone audio will degrade a 1,417 h studio model" | #1 shows exactly this (UTMOS drops). Report monolingual Hindi/English quality on IndicTTS/IndicVoices test sets; mix with clean Hindi; LoRA/low LR; this is a *result*, not a hole |
| "Your baseline is not the strongest" (#9) | Open comparison: IndicF5 zero-shot, IndicF5 + duration patch, Orato, Indic Parler. Closed systems (Bulbul v3, Gemini TTS) included in the human eval only |
| "Reference-free metrics get reward-hacked" (arXiv 2609.13150) | Position SDS as diagnostic, not RL reward; show a model that inserts pauses to zero out jumps is penalized by the divergence-from-human term |
| "UTMOS says otherwise" | UTMOS–human ρ = 0.26 on Hindi, negative on some languages (OpenBibleTTS 2026); IndicMOS degrades off-domain; MOS predictors collapse onto signal quality (Bamgbose 2026) |
| "n=30 sentences" | HiACC test split (speaker-independent, ~1,000 switches) + COMI-LINGUA sample; release ≥500 rated switch windows |

## 2.5 Importance evidence

- **Population:** ~250 M Indians code-switch daily (HiACC paper); Census 2011: 314.9 M bilinguals (26%).
- **Industry targets the switch explicitly but cannot measure it:** Sarvam Bulbul v3 (Feb 2026) is built around "people switch languages mid-sentence" (https://www.sarvam.ai/blogs/bulbul-v3); Gnani lists Hinglish segment transitions as a key TTS criterion; Gradium (Jul 2026) markets "no audible discontinuity" at switches with WER as the only proxy (https://gradium.ai/content/how-to-stop-tts-switching-accents-languages-mid-sentence).
- **Academic demand:** AI4Bharat ran 120k pairwise ratings incl. 4,164 code-mixed Hinglish sentences — the community benchmarks this, but only at utterance level. IndicF5's own code-mix eval is 30 sentences, intelligibility only.
- **Perceptual cost is real:** code-switched TTS sentences are less intelligible than monolingual ones regardless of engine (Méndez Kline & Zellou 2025).
- **Publication gap:** CALCS 2025 (NAACL) had six papers, none on TTS. Interspeech 2024–2026 accepted CS-TTS and boundary-metric papers (see 07_importance_and_venues.md).

## 2.6 Bottom line

Do it, but as: **"Natural switches are not seamless: a switch-localized, human-calibrated metric for code-switched TTS, with a Hinglish case study."** The fine-tune becomes evidence that the metric detects something global MOS cannot, and the released switch-window rating set becomes the reusable artifact.
