# 11 — Existing scores for "does this sound human?"

Every score below is in current use. For each: what it is, how it's computed, and what it misses for our problem.

## 11.1 Human listening tests (the ground truth everything else imitates)

| Score | What listeners do | Scale | Used by | Misses |
|---|---|---|---|---|
| **MOS** (Mean Opinion Score) | Rate one clip's naturalness | 1–5 | Almost every TTS paper; from ITU-T P.800 (1996, telephony) | One number per sentence; can't locate the problem |
| **QMOS / SMOS / NMOS** | MOS on one aspect: quality / speaker similarity / accent nativeness | 1–5 | Voicebox, zero-shot TTS papers | Same, per aspect |
| **CMOS** (Comparative MOS) | Hear A and B, say how much better one is | −3…+3 | F5-TTS, Flipkart Hinglish TTS | Needs pairs; still whole-sentence |
| **MUSHRA** | Rate several systems at once alongside a hidden real recording and a bad anchor | 0–100 | AI4Bharat (IndicF5, Rasa) | Whole-sentence; expensive |
| **AB preference** | "Which do you prefer?" | % preferred | AI4Bharat Voice-First Nation (120k votes, 4,164 Hinglish sentences) | Utterance-level; no reason given |
| **Intelligibility tests** | Type what you heard | % correct | Méndez Kline & Zellou 2025 | Measures understanding, not naturalness |

**Why they're the gold standard:** they measure perception directly. **Why they don't scale:** each system comparison needs new listeners, time, and money.

## 11.2 Automatic MOS predictors (a neural network guesses the MOS)

| Score | How it's built | Trained on | Misses |
|---|---|---|---|
| **UTMOS / UTMOSv2** | wav2vec2 + BLSTM, clipped-MSE + contrastive loss, stacked ensemble with simple regressors | English BVCC (~7k rated clips) | Agrees with humans at only ρ = 0.26 on Hindi; negative on some languages |
| **DNSMOS** | CNN on spectrogram | Noise-suppression ratings (ITU P.835) | Built for denoising, not TTS naturalness |
| **NISQA** | CNN + attention; outputs overall + noisiness, coloration, **discontinuity**, loudness | Telephony / VoIP ratings | Its "discontinuity" is packet loss, not prosody; utterance-level |
| **SQUIM** (torchaudio) | Predicts PESQ, STOI, SI-SDR, and a MOS without a reference | Simulated degradations | Signal quality, not prosody |
| **SQuId** (Google) | Multilingual MOS predictor, >1M ratings, 65 locales | Google internal | Closed; still utterance-level |
| **IndicMOS** (Interspeech 2024) | MOS predictor for 7 Indian languages | LIMMITS 2023/24 ratings | Degrades on unseen languages; no code-switched test |
| **Audiobox Aesthetics** | Four axes: production quality, complexity, enjoyment, usefulness | Mostly English + music | Aesthetics, not naturalness of switches |
| **SpeechLMScore** | Likelihood of the speech under a speech language model | Unlabelled speech | Weak correlation off-domain |

Shared problem (Bamgbose et al. 2026): these predictors "collapse onto acoustic signal quality" and miss prosody, pausing, and rhythm errors.

## 11.3 Reference-based signal measures (need the exact matching real recording)

| Score | Measures | Why weak for TTS |
|---|---|---|
| **PESQ / POLQA** | Perceived telephone quality vs reference | A synthesized sentence has no time-aligned real twin |
| **STOI** | Intelligibility vs reference | Same |
| **SI-SDR** | Signal-to-distortion ratio | Same |
| **MCD** (mel-cepstral distortion) | Spectral distance frame by frame | Needs alignment to a reference; ignores prosody |
| **F0 RMSE** | Pitch error vs reference | Penalizes valid alternative intonation |

Used mainly for codecs and vocoders (e.g. Qwen3-TTS's tokenizer table), where a reference exists.

## 11.4 Proxy measures reported with MOS in almost every TTS paper

| Score | How | Tells you |
|---|---|---|
| **WER / CER** | An ASR system transcribes the output; compare with input text | Intelligibility / content errors |
| **SIM** | Cosine similarity of speaker embeddings (WavLM, ECAPA) with the reference clip | Voice match |
| **FAD** (Fréchet Audio Distance) | Distance between embedding distributions of real and synthetic sets | Set-level realism, no per-clip diagnosis |
| **Audio-LLM judge** | A large audio model rates the clip (EmergentTTS-Eval) | Flexible, but opaque and unvalidated for Hindi |
| **Instruction scores** (APS, DSD, RP) | Whether the voice follows a text description (InstructTTSEval) | Controllability, not naturalness |

Qwen3-TTS (2026) reports only WER/CER and SIM for generated speech; UTMOS/PESQ/STOI appear only for its codec.

## 11.5 Scores that look at something local (closest to SDS)

| Score | What it localizes | Gap SDS fills |
|---|---|---|
| **Join cost** (Hunt & Black 1996; Vepa & King) | Spectral/F0/energy jump at unit-selection joins | Not calibrated to human switch behaviour; assumes smaller is better |
| **MagpieTTS-LF PBD** (Interspeech 2026) | F0/energy jump at long-form chunk boundaries | Chunk boundaries, not language switches; not human-validated |
| **CMI_speech** (Yeo 2026) | Frame-level language mixing index | Measures language balance, not naturalness; needs ground truth |
| **LCG localized metrics** (EMNLP 2026) | Accent nativeness of the embedded phrase | Accent only, no prosodic continuity |
| **Duration-abnormal rate** (Zuo 2026) | Utterances with abnormal duration | Utterance-level |
| **Frame-level MOS** (Kuhlmann 2025) | Where in the clip quality drops | Generic distortions, not switches |

## 11.6 The gap in one line

Every current score either rates the whole sentence, needs a matching real recording, or measures a local jump assuming "smaller is better". None measures whether a language switch carries the signature real bilinguals produce.
