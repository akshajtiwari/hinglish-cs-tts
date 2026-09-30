# 04 — Local events: finding and measuring switches

The local-event branch looks at brief moments where synthetic speech often goes wrong. Version 1 handles **language switches**; later versions add seams between generated chunks, names, and numbers. This file covers why switches matter, how they're found, and how each feature is computed. These features feed the model (`05_architecture.md`) and produce the plain-language explanation. No human labels are needed here.

## 4.1 What natural switches sound like (the scientific basis)

Real bilinguals do **not** switch smoothly. A good TTS reproduces the human switch signature; a bad one erases it (flat, seam) or exaggerates it (artificial pause, reset).

| Finding | Evidence | Implication |
|---|---|---|
| Speakers **slow down before** a switch; listeners use it to anticipate | Fricke, Kroll & Dussias 2016, *J. Mem. & Lang.* (Bangor Miami) | Look at the pre-switch side; deceleration is expected |
| Switched word has **higher pitch, wider range, longer duration** | Olson 2012, 2016; Muldner et al. 2019; Wang, Xu & Franich, Speech Prosody 2026 | A pitch/duration "bump" is natural; its absence is the defect |
| Pitch coarticulation **before** the switch word | Shen, Gahl & Johnson 2020; Piccinini & Garellek 2014 | Pre-switch pitch shape carries cues |
| **Splicing out cues hurts comprehension** | Shen et al. 2020 | Exactly the failure of join-style TTS; also a validation paradigm |
| Switches cluster at **intonation-unit boundaries** | Torres Cacoullos 2020; EMNLP 2023 IU metrics | Pauses/pitch resets at phrase boundaries are legitimate; group by position |
| Hesitations near switches are framing devices | Hlavac 2011 | Don't penalize pausing per se |
| **Hinglish:** embedded English is slower, louder, more pitch-variable | Rao et al., IIT Bombay, Interspeech 2018 | Model direction (Hi→En vs En→Hi) separately |
| The **return** to the matrix language is also marked | Wang et al. 2026 | Score both edges of an English stretch |
| Consonant (VOT) drift is **diffuse**, not local | Piccinini & Arvaniti 2015 | Keep VOT out of the boundary features |
| Code-switched speech is acoustically less stable | Zeng 2025, *JASA* | Instability ≠ unnaturalness |
| Indian English has its own rhythm | Sirsa & Redford 2013 | English-side norms = Indian English |

## 4.2 Pipeline

1. **Normalize audio:** resample to 16 kHz, low-pass at 8 kHz, loudness-normalize. (HiACC is 16 kHz; TTS output up to 24 kHz. Matching bandwidth prevents features detecting "synthetic" from bandwidth alone.)
2. **Tag words:** split transcript; language from script (or a word-level tagger, `03_datasets.md` §3.7).
3. **Align:** uroman romanizes the transcript; MMS forced alignment (torchaudio `MMS_FA`) gives each word's start/end and a confidence. Drop low-confidence words.
4. **Boundaries:** every adjacent word pair is a **switch** (languages differ) or **ordinary**. Record direction and position (phrase boundary if pause ≥150 ms or punctuation; else mid-phrase).
5. **Features** at every boundary (25 ms frames, 10 ms hop), 4.3.
6. **Contrast:** each switch's features minus the same features at the clip's ordinary boundaries (z-scored if ≥3 ordinary boundaries). Removes speaker, microphone, and style differences.
7. **Output:** a feature vector per switch for the model, plus a human-readable diagnosis.

## 4.3 Features and how each is computed

| Feature | Computation |
|---|---|
| `pause_ms` | start(B) − end(A) from the aligner; refined by frames >35 dB below the clip's peak within ±150 ms (aligners absorb short pauses) |
| `pre_rate_ratio`, `post_rate_ratio` | Syllables/second in the last (first) 1–2 words before (after) the boundary ÷ clip rate. Syllables: Hindi = independent vowels + consonants not followed by halant; English = CMU dictionary, fallback vowel groups. Cross-check with de Jong & Wempe acoustic syllable nuclei |
| `lengthening` | duration(B) ÷ (syllables(B) × speaker's mean syllable duration in the clip) |
| `f0_jump_st` | Pitch from Praat (Parselmouth) and PENN, 60–400 Hz; keep frames where both agree within 50 cents (removes octave errors); semitones vs speaker median; median of last 100 ms voiced frames of A minus first 100 ms of B (nearest voiced within 150 ms if an edge is unvoiced) |
| `f0_range_ratio` | (90th − 10th percentile semitones of B) ÷ mean range of surrounding matrix-language words |
| `f0_slope_pre` | Linear-fit slope (st/s) over the last 200 ms of A |
| `energy_jump_db`, `energy_word_db` | 20·log10(RMS); last 100 ms of A vs first 100 ms of B (voiced frames); B's mean vs clip mean |
| `mcd_jump`, `kl_jump` | 13 MFCCs without c0; mean of last 3 speech frames of A vs first 3 of B; mel-cepstral distance and symmetric KL of power spectra (classic join-cost measures) |

Missing values (e.g. fully unvoiced word) are NaN, never 0.

## 4.4 SwitchLM (label-free signal)

A small Transformer over word-level prosody tokens (pitch statistics, duration, energy, pause, pooled accent features), conditioned on words, language tags, and left context, trained only on natural code-switched speech (HiACC reference speakers, MUCS). Its **surprisal** at each switch (how unexpected it sounds) is one more input to the local branch. Evidence (TTScore-pro, SOMOS SRCC ≈0.05) says such a signal is weak alone, so it's a feature, not a metric.

## 4.5 Controls (built from natural speech; also free training pairs)

| Control | How | Tests |
|---|---|---|
| Spliced | Same speaker's Hindi and English segments joined, 10 ms crossfade | Seam detection |
| Under-marked | Slowdown, lengthening, pitch bump flattened (Praat PSOLA) | "Robotic" switches |
| Over-marked | Inserted 300 ms pause or pitch reset | Exaggeration |
| Resynthesis-only | PSOLA with no change | Separates tool artefacts from real effects |

## 4.6 Go/no-go: the natural-signature check

On HiACC reference speakers: do switches differ from ordinary boundaries as 4.1 predicts? Pre-registered pass: at least two of pre-switch slowing (rate ratio < 1), lengthening > 1, wider pitch range > 1, louder embedded English > 0 dB, significant across speakers. If not, the local branch uses learned embeddings only.

## 4.7 Tools

torchaudio `MMS_FA` + `uroman` (or `ctc-forced-aligner --romanize`), `praat-parselmouth`, `penn`, `librosa`, `numpy`/`scipy`. CPU; a few clips per second. Aligner accuracy target: median boundary error ≤25 ms on 20 hand-checked switches.
