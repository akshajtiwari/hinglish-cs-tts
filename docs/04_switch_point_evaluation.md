# 04 — Switch-Point Evaluation: the Switch Discontinuity Score (SDS), v1 design

Grounded in the phonetics, join-cost, partial-spoof, and MOS-predictor literature surveyed 2026-09-23. Replaces the v0 sketch ("less discontinuity = better"), which the evidence does not support.

## 4.1 What natural code-switches actually sound like

| Finding | Evidence | Implication for SDS |
|---|---|---|
| Speakers **slow down before** a switch; listeners use it to anticipate | Fricke, Kroll & Dussias 2016, *J. Mem. & Lang.* (Bangor Miami, spontaneous) — https://www.sciencedirect.com/science/article/abs/pii/S0749596X15001187 | Window must extend to the pre-switch side; rate deceleration is *expected* |
| Switched word has **higher pitch, wider range, longer duration** (hyper-articulation) | Olson 2012 *LAB*; Olson 2016 *IJB* — https://docs.lib.purdue.edu/context/lcpubs/article/1010/viewcontent/Olson__2016_.pdf ; Muldner et al. 2019 *IJB*; Wang, Xu & Franich, Speech Prosody 2026 — https://www.isca-archive.org/speechprosody_2026/wang26_speechprosody.pdf | An F0/duration "bump" at the switch is natural; its absence is the defect |
| F0 / tonal **coarticulation before** the switch word | Shen, Gahl & Johnson 2020 *BLC*; Piccinini & Garellek, Speech Prosody 2014 | Pre-switch F0 shape carries cues |
| **Splicing out cues hurts comprehension** | Shen et al. 2020 (concept monitoring + eye-tracking) | Exactly the failure of concatenation-style TTS; also a validation paradigm |
| Switches cluster at **intonation-unit boundaries**; "prosodic distancing" | Torres Cacoullos 2020 *Frontiers Psych.* — https://pmc.ncbi.nlm.nih.gov/articles/PMC7538515/ ; EMNLP 2023 IU metrics — https://aclanthology.org/2023.emnlp-main.1047/ | Stratify by boundary type; pauses/F0 resets at IU boundaries are legitimate |
| Hesitations near switches act as framing devices, not defects | Hlavac 2011 *J. Pragmatics* | Do not penalize pausing per se |
| **Hinglish:** embedded English is slower, louder, more pitch-variable than surrounding Hindi | Rao, Pandya, Sabu, Kumar, Bondale, IIT-B, Interspeech 2018 — https://www.isca-archive.org/interspeech_2018/rao18_interspeech.html ; dataset https://www.ee.iitb.ac.in/student/~daplab/datasets/code_switch.html | Model direction asymmetry (Hi→En vs En→Hi); reference distribution must be Hinglish-specific |
| The **return** to the matrix language is also marked | Wang et al. 2026 | Score both edges of an embedded island |
| Segmental VOT drift is **diffuse** over the bilingual stretch, not local | Piccinini & Arvaniti 2015 *J. Phonetics* | Keep VOT/aspiration out of the boundary metric |
| CS speech is acoustically *less* stable than monolingual | Zeng 2025 *JASA* | Instability ≠ unnaturalness |
| Indian English has its own rhythm; L1 timing not carried over | Sirsa & Redford 2013 *J. Phonetics* | English-side norms = Indian English, not US/UK |
| Clean, immediate segmental switch (VOT) | Grosjean & Miller 1994 | Sharp *segmental* change is fine; do not penalize |

**Conclusion:** listeners value *cue-consistent* discontinuity. A good CS-TTS reproduces the human switch signature; a bad one either erases it (seam, flat) or exaggerates it (artificial pause, reset).

## 4.2 SDS v1 definition

For each switch point *s* in an utterance, anchored on forced-aligned word boundaries:

**Windows.** Asymmetric, syllable-anchored: pre-switch = last 2 syllables of the outgoing-language word(s) (≈ 300–400 ms), post-switch = first 2 syllables of the incoming word(s). Also compute a multi-resolution variant (±160 / ±320 / ±640 ms, cf. PartialSpoof) for robustness to alignment jitter.

**Feature vector f(s)** (all computed identically on natural and synthetic speech):

| Family | Features | Ancestor |
|---|---|---|
| Rate | syllable rate pre vs post; pre-switch deceleration ratio vs utterance mean | Fricke 2016; de Jong & Wempe 2009 |
| Duration | switched-word duration z-score vs same word length class in utterance; pause duration at boundary | Olson 2016; Muldner 2019 |
| F0 | ΔF0 across boundary (semitones), F0 range in switched word vs matrix mean, pre-switch slope; two trackers (PENN + Praat) with agreement check | Olson; MagpieTTS-LF PBD |
| Energy | ΔRMS (dB) across boundary; switched-word mean energy vs matrix | Rao 2018; Hunt & Black join cost |
| Spectral | mel-cepstral distance and symmetric KL of spectra across the boundary frame pair | Klabbers & Veldhuis; Stylianou & Syrdal; Negroni 2024 |
| Voice quality (optional) | jitter/shimmer/HNR jump | Zeng 2025 |

**Within-utterance normalization.** For every feature, subtract/scale by the same feature computed at *non-switch* word boundaries in the same utterance → contrast vector c(s). This removes speaker, style, and recording confounds (a spontaneous-style fine-tune will have more variation *everywhere*).

**Reference distribution.** Fit the distribution of c(s) on natural Hinglish switches (HiACC adult + IIT-B code-switch dataset), stratified by (direction: Hi→En / En→Hi) × (boundary type: IU-boundary / IU-internal) × (island length: 1 word / multi-word).

**Score.** Two terms, reported separately and combined:
- **SDS-seam**: probability that the boundary is a splice, from spectral/energy jump features (never natural; calibrated on natural vs artificially spliced natural speech).
- **SDS-prosody**: Mahalanobis distance of c(s) from the matched natural-reference stratum, signed per feature into *under-marked* (flat) vs *over-marked* (exaggerated).
- Utterance/system score = mean over switches; report distributions, not just means.

**Ablations that must be in the paper:** with vs without within-utterance normalization; fixed 250 ms symmetric window vs syllable-anchored asymmetric; raw discontinuity magnitude vs distance-to-human; sensitivity to ±20 ms alignment jitter.

## 4.3 Human validation protocol

Three complementary tasks, bilingual Hindi-English raters, switch-local stimuli (≈1.5 s excerpt centred on the switch, with a 0.5 s fade, plus the full utterance available on demand):

1. **Switch-naturalness rating** (1–5) of the excerpt only — join-test design from Vepa & King 2006 and Kuhlmann et al. 2025.
2. **Region highlighting**: listener marks where in the full utterance it sounds wrong (XSQ-AST 2026 protocol); tests whether the switch is where problems concentrate.
3. **Behavioural**: word identification of the first post-switch word in noise (Méndez Kline & Zellou 2025; Shen 2020). Measures whether cues were preserved, independent of opinion.

Stimuli: ≥500 switch windows across {natural HiACC, spliced-natural control, IndicF5 zero-shot, IndicF5 + duration patch, Orato fine-tune, Indic Parler, our fine-tune, Bulbul v3, Gemini TTS}. Include *also* whole-utterance MOS so the paper can show the local–global dissociation.

Validation statistics: (i) Spearman/Kendall of SDS vs task-1 ratings *within* utterance, controlling for utterance MOS; (ii) ROC of SDS-seam for natural vs spliced; (iii) SDS vs task-3 accuracy; (iv) same for baselines: raw join cost, PBD (MagpieTTS-LF), CMI_speech (Yeo 2026), Whisper-LID confidence (LCG), duration-abnormal rate (Zuo 2026), UTMOS, NISQA discontinuity, IndicMOS.

Rater pool: 5–8 screened bilinguals is enough for correlation claims; AI4Bharat's Voice-First Nation shows large Hinglish rater pools exist if scaling is needed. Tools: webMUSHRA (https://github.com/audiolabs/webMUSHRA) or ITU P.808 toolkit (https://github.com/microsoft/P.808).

## 4.4 Why not use an off-the-shelf naturalness predictor

| Predictor | Problem |
|---|---|
| UTMOS / UTMOSv2 | ρ with human MOS = **0.26 on Hindi**, negative on Oromo/Shona (OpenBibleTTS 2026, https://arxiv.org/abs/2606.09553); English-trained |
| IndicMOS (Interspeech 2024) — https://www.isca-archive.org/interspeech_2024/udupa24b_interspeech.pdf | Only Indic predictor; degrades on unseen languages and TTS+VC (τ 0.51/0.43); no CS test set |
| SQuId (Google) | Closed |
| NISQA | Has a "discontinuity" dimension but telephony-domain, utterance-level, untested on Indic TTS |
| DNSMOS, SQUIM, Audiobox-Aesthetics | Signal quality / aesthetics, not prosodic seams |
| All MOS predictors | "Collapse onto acoustic signal quality", miss prosody/pausing (Bamgbose et al. 2026, https://arxiv.org/abs/2608.09930) |

They stay in the paper as baselines that SDS must beat on switch-local ratings.

## 4.5 Tooling

| Need | Choice | Notes |
|---|---|---|
| Forced alignment on mixed Devanagari+Latin | **MMS_FA (torchaudio) + uroman**, or `ctc-forced-aligner --romanize --language hin` | Lexicon-free, script-agnostic. torchaudio FA API deprecated in 2.8, pin version. Default ctc-forced-aligner model is CC BY-NC |
| Precision refinement | Adapt MFA on code-mixed Hinglish per Pandey, Gogoi & Tang 2026 (https://arxiv.org/abs/2607.25581): 4.15 ms vs ~38 ms monolingual | IndicMFA (AI4Bharat) has Hindi but no English; MFA has no pretrained Hindi acoustic model |
| Hand-check | Label 100 switch boundaries in Praat; report aligner boundary error |
| F0 | PENN (https://github.com/maxrmorrison/penn) + Praat/Parselmouth; report agreement | Octave errors at a boundary look like ΔF0 |
| Rate | de Jong & Wempe syllable nuclei; nPVI for rhythm | |
| Spectral | librosa MFCC / mel; symmetric KL on FFT spectra | |
| Splice control | Concatenate natural Hindi and natural English segments from the same HiACC speaker with a 10 ms crossfade | Ground truth "seam" for SDS-seam calibration |

## 4.6 Open design questions (to resolve in a pilot on 50 switches)

1. Syllable-anchored vs fixed-ms windows: which correlates better with task-1 ratings?
2. Is one reference distribution per stratum overfitting with ~1,000 natural switches? Fall back to direction-only strata if so.
3. Do Hi→En and En→Hi need different feature weights (Rao 2018 asymmetry)?
4. Does the IIT-B public-speech dataset (rehearsed) match HiACC (spontaneous) closely enough to pool as reference?
