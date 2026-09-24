# 07 — Importance, Audience, and Venues

## 7.1 Why this matters (evidence)

| Signal | Evidence |
|---|---|
| Scale of Hinglish | ~250 M Indians code-switch daily (HiACC paper, Data in Brief 2025). Census 2011: 314.9 M bilinguals (26 %). Dhoundiyal 2023 abstract cites 528 M Hinglish users |
| Industry builds for the switch but has no metric | Sarvam Bulbul v3 (Feb 2026): designed around "people switch languages mid-sentence"; code-mixing in its CER robustness set; no numbers — https://www.sarvam.ai/blogs/bulbul-v3 . Gnani: Hinglish/Tanglish segment transitions as a TTS-selection criterion — https://www.gnani.ai/resources/blogs/how-to-choose-the-right-tts-engine-for-indic-languages . Gradium (Jul 2026): markets "no audible discontinuity" at switches, WER as only proxy — https://gradium.ai/content/how-to-stop-tts-switching-accents-languages-mid-sentence |
| Deployment failure mode | Indian voice-bot vendors (Mihup, Ondial, Bolti, Caller Digital) name code-switching as the main production failure, mostly on ASR (+30–50 % relative WER) |
| Academic community already rating this at scale | AI4Bharat Voice-First Nation: 120 K+ pairwise, 1,915 raters, 4,164 code-mixed Hinglish sentences, 7 systems — https://arxiv.org/html/2604.21481v2 . Utterance-level only |
| Perceptual cost is measurable | CS TTS sentences less intelligible than monolingual regardless of engine (Méndez Kline & Zellou 2025). Removing switch cues slows comprehension (Shen et al. 2020) |
| Metric gap | No switch-local metric exists in any language pair; MOS predictors fail on Hindi (UTMOS ρ = 0.26); CALCS 2025 had zero TTS papers |
| Data augmentation demand | 2020–2026 papers use CS-TTS to train Hinglish ASR (Sharma 2020; Biswas 2025; BEHE-CMDisfl 2026) and none can measure whether the synthetic switches are realistic. Yeo 2026 shows realistic language boundaries in synthetic speech improve downstream ASR |

## 7.2 Who uses the result

1. **TTS builders** (AI4Bharat, Sarvam, Gnani, Orato, Google/ElevenLabs Indic teams): a diagnostic for the one thing they market and cannot measure.
2. **CS-ASR researchers**: a filter/critic for synthetic CS augmentation data (extends Yeo 2026's CMI_speech).
3. **Phoneticians of code-switching**: first Hindi-English switch-point acoustic distribution on spontaneous speech since Rao et al. 2018.
4. **Evaluation researchers**: another dimension-specific metric in the "beyond MOS" line (PSP 2026, Bamgbose 2026, Kuhlmann 2025).

## 7.3 Venue fit

| Venue | Precedent (2023–2026) | Fit |
|---|---|---|
| **Interspeech** | 2024: Yang et al. CS-TTS. 2025: CS-FLEURS, Gourav "Code Mix TTS", Biswas Hinglish CBA, IndicMOS (2024), Kuhlmann frame-level MOS. 2026: MagpieTTS-LF boundary metric | **Best fit.** Metric + human eval + case study is a classic Interspeech shape. Speech Prosody track also fits the phonetics angle |
| ICASSP | 2024 Speech Collage; 2025 PIER metric | Good; shorter page limit |
| SLT / ASRU | ASRU 2025 CS-LLM | Good for the fine-tuning/data-efficiency angle |
| **CALCS workshop** (NAACL/ACL) | 2025: 6 papers, **none on TTS** | Gap-filler; smaller audience but exactly the community |
| EMNLP / EMNLP Findings | 2025 UniCoM; 2026 LCG (main) | Fits if framed as evaluation methodology |
| NeurIPS D&B | 2025 SwitchLingua, EmergentTTS-Eval | Fits if the released switch-window rating set is the headline |
| Speech Prosody | 2026 Wang et al. CS prosody | Fits the phonetic-signature part; could be a companion short paper |
| SSW | 2025 Murthy keynote on code-mixed Indic synthesis | Friendly audience |
| ICON / OCOCOSDA / LREC-COLING WILDRE | 2026 WILDRE BEHE-CMDisfl | Regional fallback |

**Recommendation:** Interspeech (metric paper, 4 pages + refs) as the primary target, with the switch-window rating set + SDS code as a released artifact. If results are strong on the human-validation side, a NeurIPS D&B submission of the dataset is a second paper, not a competitor.

## 7.4 Suggested title directions

- "Natural Switches Are Not Seamless: A Switch-Localized, Human-Calibrated Metric for Code-Switched TTS"
- "Where the Language Changes: Measuring Prosodic Fidelity at Code-Switch Points in Hinglish TTS"
- "SDS: Scoring the Seam in Code-Switched Speech Synthesis"
