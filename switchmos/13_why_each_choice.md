# 13 — Why each choice (one line each)

## Goal and framing

| Choice | Why |
|---|---|
| Whole-clip score as the headline | A clip can switch well and still sound synthetic elsewhere; users need one overall number, as with UTMOS |
| Local-event branch as a component, not the goal | Brief problems get averaged away in whole-clip pooling; the branch adds that evidence and explains it |
| Beat UTMOS where it fails, not everywhere | UTMOS/UTMOSv2 are near chance on modern, clean, non-English speech; old English benchmarks are saturated |
| Research-only licence | The strongest English training data (SOMOS, BVCC, SpeechJudge) is non-commercial |

## Data

| Choice | Why |
|---|---|
| Many datasets, not one | Data diversity is the largest single lever in published ablations |
| Absolute and pairwise labels together | Absolute sets give scale; pairwise sets cover modern systems and code-switching |
| SpeechJudge-Data | Only large modern preference set with code-switched (zh–en) clips; outputs of open models |
| MANGO | Indic absolute ratings from open systems, CC-BY |
| SpeechArenaBench | Only large Indic and code-switched preference set; use pending vendor-ToS decision |
| Hold out whole systems and languages | Otherwise the model can win by recognizing the system or language |
| Our own HiACC speaker split | Shipped splits share all 24 speakers |

## Audio and features

| Choice | Why |
|---|---|
| 16 kHz, 8 kHz low-pass for switch features | HiACC is 16 kHz (content ≤8 kHz); matching stops "synthetic" being detected from bandwidth |
| 16 kHz input to encoders | What the SSL encoders and baselines expect |
| Loudness normalization | A quiet recording shouldn't look like a loudness jump |
| 25 ms frames, 10 ms hop | Standard; captures a low voice's pitch period; 100 measurements per second |
| MMS aligner + uroman | 1,100+ languages without a dictionary; uroman lets it read any script |
| Script = language | Transcripts follow it (Devanagari Hindi, Latin English); no extra model needed |
| Two pitch trackers, 50-cent agreement | Octave errors look exactly like pitch jumps |
| Semitones vs speaker median | Makes voices comparable; hearing is logarithmic |
| 100 ms edge windows, 200 ms slope window | About one syllable; captures the run-up listeners use |
| MFCC distance and symmetric KL | Classic join-cost measures; KL best predicted audible joins |
| Contrast vs ordinary boundaries | Removes speaker, mic, and style effects |
| Group by direction and position | Hi→En and En→Hi differ; pauses are normal at phrase boundaries |
| ±150 ms silence search, −35 dB threshold | Aligners absorb short pauses; a robust speech/non-speech cut |

## Model

| Choice | Why |
|---|---|
| Multilingual SSL encoder | English-trained encoders transfer poorly; SSL generalizes across languages better than codecs |
| Learned layer weights | Different layers carry quality vs intelligibility; biggest single effect in DAMOS |
| Spectrogram branch | Best absolute scores in UTMOSv2; fusion with SSL beats either |
| Dataset embedding with per-dataset bias | Reconciles MOS, MUSHRA, and pairwise scales |
| Rater embedding | Largest single effect in UTMOS |
| Switch-anchored windows for local scores | Full-context frame scores aren't truly local (Kuhlmann 2025) |
| Soft-min over events | One bad moment lowers perceived naturalness more than an average suggests |
| SwitchLM as a feature only | Label-free prosody likelihood alone correlates weakly (TTScore-pro ≈0.05) |
| No multi-level stacking | Added only +0.006 in UTMOS |

## Training

| Choice | Why |
|---|---|
| Bradley–Terry loss | Beats regression on preference data (80% vs 76%) |
| Davidson ties | Uses tied pairs that all prior work discards |
| Clipped MSE for absolute scores | UTMOS practice; ignores noise-level errors |
| Multi-stage training | Largest factor in UTMOSv2 |
| Minimal pairs for the local branch | Exact locations, no human labels; no prior quality judge uses them |
| Same vocoder on both versions | Otherwise the model learns "was vocoded" |
| Non-switch edit controls | Otherwise the model learns "was edited" |
| Data-mix ablations first | Data is the biggest lever |
| Cache features | A16s are slow; compute once |

## Evaluation

| Choice | Why |
|---|---|
| Pairwise accuracy with human ceiling | Standard for modern predictors; ceiling shows how much is achievable |
| Longest-clip baseline | Length alone scores 0.52 on clean TTS; must beat it |
| Our model trained on UTMOS's data only | Separates the effect of data from design |
| Spearman / Kendall | Human ratings are ordinal |
| Paired bootstrap | Significance without distribution assumptions |
| Krippendorff's α ≥ 0.5 | Below that, human labels are too noisy to test anything |
| Best-of-N reward-hacking test | Cheap check that the judge can't be gamed |
| Pre-registration | Prevents tuning to test results |
