# 09 — What to Study to Get This Going

Scope: the topic areas you need, the depth you need them at, and where to learn each. Not a syllabus of every detail. Depth levels: **Know** = can explain it and read papers that use it; **Do** = can run the tool and debug it; **Own** = can design and defend it in the paper.

Time estimate: 4–6 weeks part-time, interleaved with phases 0–1 of the plan. Do not finish studying before starting; each block ends with a hands-on checkpoint that is also a project task.

---

## Block 1 — Speech signals and the features SDS uses

**Why:** every term in SDS (F0, energy, rate, spectral distance) is a signal-processing quantity. You need to compute them, plot them, and know when they lie (octave errors, unvoiced frames, noise).

**Depth:** Do.

**Learn**
- Waveform, sampling rate (why 16 kHz vs 24 kHz matters), framing, windowing, STFT, mel spectrogram, MFCCs.
- Fundamental frequency (F0 / pitch): what it is, voiced vs unvoiced, semitones vs Hz, octave errors, why you run two trackers.
- Energy / RMS / dB; intensity contours.
- Speech rate: syllables per second, pauses, articulation rate vs speech rate.
- Spectral distance between two frames (mel-cepstral distance, KL between spectra).
- Voice onset time and aspiration: only enough to know why they are *excluded* from the boundary metric.

**Resources**
- Jurafsky & Martin, *Speech and Language Processing* 3rd ed. draft, the phonetics chapter and the ASR/TTS chapter — https://web.stanford.edu/~jurafsky/slp3/
- librosa documentation and tutorial notebooks — https://librosa.org/doc/latest/
- Parselmouth (Praat in Python) examples — https://parselmouth.readthedocs.io/
- Praat itself, "Intro" manual pages on pitch and intensity — https://www.fon.hum.uva.nl/praat/
- PENN pitch tracker README — https://github.com/maxrmorrison/penn
- de Jong & Wempe 2009 syllable-nuclei speech-rate script — https://sites.google.com/site/speechrate

**Checkpoint:** open 5 HiACC files in Praat, mark the switches by ear, then reproduce the F0/intensity/rate contours in Python and overlay them. Your Python F0 and Praat's should agree on voiced frames.

---

## Block 2 — Prosody and the phonetics of code-switching

**Why:** the paper's central claim is "natural switches are marked, not seamless." You must be able to state what the literature found, in which language pairs, and what it predicts for Hinglish.

**Depth:** Know (Own for the five key papers).

**Learn**
- Prosody vocabulary: intonation unit, pitch reset, final lengthening, pitch range, declination, prosodic boundary vs word boundary.
- Hyper-articulation (H&H theory) as an explanation for switched-word marking.
- Matrix vs embedded language; insertional vs alternational switching; intra-sentential vs inter-sentential.
- Code-Mixing Index (CMI) and switch-point fraction as text-side metrics.
- Indian English rhythm as the English-side norm.

**Read (in this order)**
1. Sitaram, Chandu, Rallabandi & Black 2019, *A Survey of Code-switched Speech and Language Processing* — https://arxiv.org/abs/1904.00784 (orientation)
2. Rao et al. 2018, Hindi-English prosodic cues — https://www.isca-archive.org/interspeech_2018/rao18_interspeech.html (Own)
3. Fricke, Kroll & Dussias 2016, pre-switch slowing — https://www.sciencedirect.com/science/article/abs/pii/S0749596X15001187 (Own)
4. Olson 2016, suprasegmental marking of switched words — https://docs.lib.purdue.edu/context/lcpubs/article/1010/viewcontent/Olson__2016_.pdf (Own)
5. Torres Cacoullos 2020, prosodic distancing — https://pmc.ncbi.nlm.nih.gov/articles/PMC7538515/ (Own)
6. Shen, Gahl & Johnson 2020, withholding switch cues — Cambridge BLC (Own)
7. Wang, Xu & Franich 2026, Speech Prosody — https://www.isca-archive.org/speechprosody_2026/wang26_speechprosody.pdf
8. Olson 2024 handbook chapter (review) — Cambridge Handbook of Bilingual Phonetics and Phonology, ch. 30

**Checkpoint:** write one page, in your own words, predicting what F0, rate, energy, and pause should do at a Hi→En switch and at the return, with a citation per prediction. This page becomes §2 of the paper.

---

## Block 3 — Forced alignment

**Why:** SDS needs word boundaries at ~20 ms precision. HiACC has none. Alignment error is the single biggest technical risk to the metric.

**Depth:** Do (Know the theory).

**Learn**
- What forced alignment is; the difference from ASR.
- CTC alignment (how a CTC model gives frame-level character posteriors, and how Viterbi over them yields boundaries).
- HMM-GMM alignment as in MFA, and why it is more precise on boundaries.
- Romanization (uroman) as the trick that makes mixed-script text alignable.
- How to measure aligner accuracy against hand labels.

**Resources**
- torchaudio forced-alignment tutorial for multilingual data (MMS + uroman) — https://docs.pytorch.org/audio/2.8/tutorials/forced_alignment_for_multilingual_data_tutorial.html
- ctc-forced-aligner README — https://github.com/MahmoudAshraf97/ctc-forced-aligner
- Montreal Forced Aligner docs, "first steps" — https://montreal-forced-aligner.readthedocs.io/
- Pandey, Gogoi & Tang 2026, forced alignment of Hindi-English code-mixed speech — https://arxiv.org/abs/2607.25581 (Own; this is your precision benchmark)
- Rousso et al. 2024, comparison of modern FA methods — https://arxiv.org/abs/2406.19363
- CTC explained: Hannun, "Sequence Modeling with CTC", Distill 2017 — https://distill.pub/2017/ctc/

**Checkpoint:** align 20 HiACC files with MMS + uroman, hand-label 20 switch boundaries in Praat, report median absolute error. Decide whether MFA adaptation is needed.

---

## Block 4 — How modern zero-shot TTS works (F5-TTS family)

**Why:** you will fine-tune one, patch its inference code, and explain in the paper why byte-counting breaks it. You do not need to derive flow matching; you need the mental model.

**Depth:** Know (Do for the codebase).

**Learn**
- The pipeline: text → character tokens → transformer (DiT) conditioned on reference mel + text → mel spectrogram → vocoder (Vocos) → waveform.
- In-context / infilling formulation: the model sees reference audio + reference text + target text and fills in the masked target audio. Why this gives zero-shot voice cloning.
- Flow matching at the level of "learn a velocity field that moves noise to data; sample by ODE integration in N steps"; classifier-free guidance; why the output length must be fixed *before* generation (this is where the duration bug lives).
- Character-level tokenizers and custom vocab files; why an unseen character is a random embedding.
- Mel-spectrogram vocoders (Vocos) at the level of input/output.
- LoRA: what it changes, why it fits in small GPUs, when full fine-tuning is worth it.

**Resources**
- F5-TTS paper — https://arxiv.org/abs/2410.06885 (Own §3)
- Voicebox paper (the infilling + flow-matching idea F5 builds on) — https://arxiv.org/abs/2306.15687 (Know)
- Lipman et al. 2022, *Flow Matching for Generative Modeling* — https://arxiv.org/abs/2210.02747 (skim §1–3; skip proofs)
- A gentle flow-matching explainer: Tor Fjelde et al., "An Introduction to Flow Matching" (Cambridge MLG blog) — https://mlg.eng.cam.ac.uk/blog/2024/01/20/flow-matching.html
- IndicF5 paper "Phir Hera Fairy" — https://arxiv.org/abs/2505.20693 (Know what data it saw)
- LoRA paper — https://arxiv.org/abs/2106.09685 (skim)
- The code: `src/f5_tts/infer/utils_infer.py` and `src/f5_tts/model/` in https://github.com/SWivid/F5-TTS — read them with the paper open

**Checkpoint:** run IndicF5 inference on one Hinglish sentence, then trace by hand how `duration` was computed for it, and reproduce the truncation on a Latin-heavy sentence.

---

## Block 5 — Fine-tuning practice

**Why:** phase 5 of the plan. Most failures here are engineering, not science.

**Depth:** Do.

**Learn**
- Dataset preparation for F5-TTS: CSV `audio_file|text`, resampling, loudness normalization, silence trimming, transcript cleaning.
- Training loop knobs: learning rate, warmup, batch by frames, gradient accumulation, EMA (and why to disable it early), mixed precision and why bf16 produced NaNs for others, checkpoint selection.
- GPU memory budgeting; renting a cloud A100; saving to persistent storage.
- Experiment tracking (Weights & Biases or plain CSV + git tags) and seeding for reproducibility.
- Overfitting signs on 3 h of data; how to hold out speakers.

**Resources**
- F5-TTS training/fine-tuning README — https://github.com/SWivid/F5-TTS/blob/main/src/f5_tts/train/README.md
- F5-TTS discussion #57 "Finetune practice" and #769 (small-data reports) — https://github.com/SWivid/F5-TTS/discussions/57
- Orato model card (a worked IndicF5 fine-tune with its hyperparameters) — https://huggingface.co/tryorato/orato-tts-hindi-v1
- F5-TTS LoRA repo — https://github.com/instavar/f5-tts-lora-finetuning
- HuggingFace course, "fine-tuning" and "PEFT" chapters — https://huggingface.co/learn

**Checkpoint:** a 200-step LoRA fine-tune on 30 minutes of HiACC that runs end to end, saves a checkpoint, and synthesizes one sentence. Quality irrelevant; the pipeline is the deliverable.

---

## Block 6 — Evaluation methodology and statistics

**Why:** the paper is a metric paper. Its credibility is entirely in how the human test is designed and how the correlation is reported.

**Depth:** Own.

**Learn**
- Listening-test formats: MOS, CMOS, MUSHRA, AB/ABX preference; what each can and cannot show. How many listeners and stimuli you need.
- Local (segment-only) rating designs and the join-cost validation tradition.
- Behavioural tasks: word identification in noise as an objective complement to ratings.
- Rater screening, attention checks, randomization, counterbalancing.
- Inter-rater reliability: Krippendorff's α, ICC.
- Correlation: Spearman ρ, Kendall τ, and why system-level vs utterance-level correlation differ; partial correlation (controlling for utterance MOS).
- Classification-style validation: ROC / AUC for "natural vs spliced".
- Distances: z-scores, Mahalanobis distance, why you need enough reference samples per stratum.
- Confidence intervals by bootstrap; multiple-comparison awareness.
- Why off-the-shelf MOS predictors are not ground truth (and how to use them as baselines).

**Resources**
- Wester, Valentini-Botinhao & Henter 2015, *Are we using enough listeners? No!* — https://www.isca-archive.org/interspeech_2015/wester15_interspeech.html (Own)
- ITU-T P.808 crowdsourced MOS and Microsoft's toolkit — https://github.com/microsoft/P.808
- webMUSHRA — https://github.com/audiolabs/webMUSHRA
- Vepa & King 2006, subjective evaluation of join cost — https://scispace.com/pdf/subjective-evaluation-of-join-cost-and-smoothing-methods-for-4z0f1iudsi.pdf (Own; the template for switch-only rating)
- Kuhlmann et al. 2025, frame-level quality with crowdsourced localization — https://arxiv.org/abs/2508.10374
- Méndez Kline & Zellou 2025, word-ID after a switch — Frontiers CS (Own; the behavioural task)
- Krippendorff's α: `krippendorff` Python package docs; Hayes & Krippendorff 2007 paper
- scipy.stats documentation for spearmanr, kendalltau, bootstrap
- OpenBibleTTS 2026, Table 3 (UTMOS fails on Hindi) — https://arxiv.org/abs/2606.09553
- IndicMOS, Interspeech 2024 — https://www.isca-archive.org/interspeech_2024/udupa24b_interspeech.pdf

**Checkpoint:** a written pilot protocol (stimulus list, rater instructions in Hindi/English, screening, analysis script that outputs α, ρ, and bootstrap CIs on fake data) before any real rater hears anything.

---

## Block 7 — ASR-based intelligibility metrics and Hindi-English text handling

**Why:** CER via ASR is the secondary metric everyone expects; getting it right for mixed script is fiddly. Script policy is also an experimental variable.

**Depth:** Do.

**Learn**
- Whisper and IndicConformer for Hindi; word/character error rate; why CER needs script normalization for Hinglish (the same word can be transcribed in Devanagari or Latin).
- Unicode and Devanagari: combining marks, nukta, chandrabindu, normalization forms.
- Transliteration with IndicXlit; loanword override tables; the limits of transliterating English.
- Token-level language ID for Hinglish; CMI computation.
- Multi-ASR consensus scoring (the harrrshall rubric) and its blind spots.

**Resources**
- Whisper paper — https://arxiv.org/abs/2212.04356 ; `jiwer` package for WER/CER
- IndicXlit repo — https://github.com/AI4Bharat/IndicXlit ; IndicNLP library for normalization — https://github.com/anoopkunchukuttan/indic_nlp_library
- harrrshall/hinglish-tts eval rubric and scripts — https://github.com/harrrshall/hinglish-tts
- COMI-LINGUA dataset card (token LID conventions) — https://huggingface.co/datasets/LingoIITGN/COMI-LINGUA
- Gambäck & Das 2014 (CMI definition) — search "Code-Mixing Index Gambäck Das"

**Checkpoint:** compute normalized CER for one synthesized sentence under both script policies with two ASR engines, and explain any disagreement.

---

## Block 8 — Reading the code-switched TTS literature critically

**Why:** the related-work section must position SDS against three 2026 papers and the join-cost tradition without overclaiming.

**Depth:** Know (Own for the four starred).

**Read**
- ★ Lee et al. 2026, LCG — https://arxiv.org/abs/2609.01016
- ★ Ghosh et al. 2026, MagpieTTS-LF (Prosodic Boundary Discontinuity) — https://arxiv.org/abs/2606.18485
- ★ Yeo et al. 2026, CMI_speech — https://arxiv.org/html/2606.19381 ; and Yeo et al. 2025 APSIPA — https://arxiv.org/abs/2601.00935
- ★ Hunt & Black 1996 join cost (any summary; the Pearson sample chapter linked in 04)
- Thomas et al. 2018, Indic code-switching synthesizers — https://www.isca-archive.org/interspeech_2018/thomas18_interspeech.pdf
- Joshi & Garera 2023, Flipkart Hinglish TTS — https://arxiv.org/abs/2312.01103
- Anand et al. 2026, Voice-First Nation — https://arxiv.org/html/2604.21481v2
- Das, Williams & Lai 2022 (stratifying by switch count) — https://arxiv.org/abs/2203.14640
- Bamgbose et al. 2026, *Beyond Naturalness* — https://arxiv.org/abs/2608.09930

**Checkpoint:** a one-paragraph "how SDS differs" note for each starred paper. These paragraphs go straight into related work.

---

## Block 9 — Research engineering and ethics hygiene

**Why:** gated models, licensed data, human raters, and a release all have paperwork.

**Depth:** Do.

**Learn**
- HuggingFace gated-model access and tokens; keeping secrets out of git.
- Dataset licenses (CC BY vs BY-NC vs BY-SA) and what each permits for models and demos.
- Basic human-subjects practice for listening tests: consent text, no PII, fair pay for raters, your institution's ethics process if any.
- Reproducibility: pinned environments (Python ≤3.11 for IndicXlit's fairseq), seeds, config files, a `RESULTS.md` that records every number with the command that produced it.
- Releasing code and data: README, license choice, model card.

**Resources**
- Creative Commons license chooser and FAQ — https://creativecommons.org/faq/
- HuggingFace model-card and dataset-card guides — https://huggingface.co/docs/hub/model-cards
- Interspeech author kit and page limits — https://www.isca-archive.org/ (current year's call)

**Checkpoint:** a repo skeleton with `data/` ignored, `configs/`, `sds/`, `scripts/`, `RESULTS.md`, and a `LICENSE`, plus the HiACC license email sent.

---

## Block 10 — Writing a metric paper

**Why:** metric papers are judged on validation, not on the model.

**Depth:** Know.

**Learn**
- The standard shape: motivation (the blind spot) → what natural behaviour looks like → metric definition → human validation → bake-off vs existing metrics → case study → limitations.
- How to report negative and mixed results (quality drops after fine-tune) so reviewers trust you.
- Interspeech 4-page discipline: one figure that shows the local–global dissociation, one table for the bake-off, one for the case study.

**Resources**
- Read two accepted metric papers end to end as templates: IndicMOS (Interspeech 2024) and Kuhlmann et al. (Interspeech 2025), both linked above.
- Simon Peyton Jones, "How to write a great research paper" (talk/slides) — widely mirrored; search the title.

**Checkpoint:** a one-page outline with the three planned figures/tables sketched as empty placeholders.

---

## Suggested order

| Weeks | Blocks | Runs alongside plan phase |
|---|---|---|
| 1 | 1, 9 | 0 (setup, license email, gated access) |
| 2 | 3, 2 | 1 (alignment pilot) |
| 3 | 2, 6 | 2 (natural switch signature) |
| 4 | 4, 7 | 3 (baselines) |
| 5 | 6, 8 | 4 (SDS pilot) |
| 6 | 5, 10 | 5 (fine-tune) |

## What you can skip

- Deriving flow matching or diffusion theory.
- Vocoder internals.
- Training a TTS from scratch.
- Deep phonology or Hindi grammar; only the switch-relevant prosody matters.
- Any other language pair's corpora beyond the papers listed.
