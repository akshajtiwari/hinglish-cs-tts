# 12 — Why each technical choice (one line each)

| Choice | What it is | Why |
|---|---|---|
| **16 kHz** | Sample rate: 16,000 measurements of the waveform per second | HiACC was recorded at 16 kHz, so it's the highest rate every clip genuinely has |
| **8 kHz low-pass** | Remove all sound above 8,000 Hz | A 16 kHz recording can only hold sound up to 8 kHz (half the rate); TTS output has sound up to 12 kHz, which would reveal "synthetic" by bandwidth alone |
| **24 kHz** | IndicF5's native output rate | Fixed by the model's vocoder; only matters for the fine-tune, not for SDS |
| **Loudness normalization** | Scale every clip to the same average level | So a quiet recording isn't mistaken for a loudness jump |
| **25 ms frame** | Length of each analysis slice | Long enough to capture a pitch period of low voices (60 Hz = 17 ms), short enough that speech is roughly stable inside it |
| **10 ms hop** | Spacing between frames | Standard in speech; gives 100 measurements per second, finer than any prosodic event |
| **MMS aligner** | Meta's multilingual forced aligner | Handles 1,100+ languages without a pronunciation dictionary |
| **uroman** | Converts any script to Latin letters | MMS only reads Latin letters; uroman makes mixed Devanagari+Latin alignable |
| **Script = language** | Devanagari → Hindi, Latin → English | HiACC transcripts follow this convention, so no language-ID model is needed |
| **±150 ms silence search** | Where to look for a pause around a boundary | Aligners often absorb short pauses into words; 150 ms covers typical inter-word pauses |
| **−35 dB silence threshold** | Frames this far below the loudest frame count as silence | A common, robust speech/non-speech cut for clean-ish recordings |
| **Syllable counting** | Hindi from vowel signs; English from CMU dictionary | Speaking rate is syllables per second; words vary too much in length to count words |
| **60–400 Hz pitch range** | Allowed F0 search range | Covers adult male and female speech; excludes most tracker errors |
| **Two pitch trackers** | Praat and PENN, keep frames where they agree | Octave errors look exactly like pitch jumps; agreement removes them |
| **50 cents agreement** | Half a semitone | Tight enough to reject octave errors, loose enough for normal tracker noise |
| **Semitones vs speaker median** | Log pitch scale relative to the speaker | Makes male and female voices comparable; hearing is logarithmic |
| **100 ms edge windows** | How much of each word's edge is measured | About one syllable; the switch cue sits at the word edge |
| **200 ms slope window** | Pitch trend before the switch | Captures the run-up that listeners use to anticipate a switch |
| **13 MFCCs, drop c0** | Compact spectrum description, minus overall level | Standard spectral representation; c0 duplicates the loudness feature |
| **3 frames each side** | Averaging for the spectral jump | Smooths single-frame noise while staying at the boundary |
| **MCD and symmetric KL** | Two spectral distances | MCD is the standard; KL best predicted audible joins in listening studies |
| **Contrast vs ordinary boundaries** | Switch minus same-sentence non-switch boundaries | Removes speaker, microphone, and speaking-style differences |
| **Groups by direction** | Separate references for Hi→En and En→Hi | Phonetics shows the two directions behave differently |
| **Groups by position** | Phrase boundary vs mid-phrase | Pauses and pitch resets are normal at phrase boundaries, not mid-phrase |
| **Ledoit–Wolf shrinkage** | A stabilized covariance estimate | Plain covariance is unreliable with ~10 features and a few hundred samples |
| **Mahalanobis distance** | Distance that accounts for correlated features | Pause and pitch reset often co-occur; plain distance would double-count |
| **Percentile scale** | Score = share of natural switches that are more typical | Makes numbers interpretable: 50 = typical human, 95 = rarer than 95% of humans |
| **90% in-range** | A switch counts as "natural" if within the central 90% of real switches | A conventional two-sided band; real speech scores 0.90 by construction |
| **Leave-one-speaker-out** | Build percentiles without the speaker being scored | So the reference reflects unseen speakers, like a test set |
| **Speaker-disjoint FT / REF / TEST** | Each speaker in one role only | Prevents the fine-tune from scoring well by imitating reference voices |
| **10 ms crossfade in splices** | Blend at the join of a spliced control | Removes the click, leaving a realistic seam rather than a trivial one |
| **300 ms inserted pause** | The over-marked control | Clearly longer than typical switch pauses, but plausible |
| **PSOLA** | Praat's method for changing pitch and duration | Standard, well-understood manipulation for building controls |
| **Resynthesis-only control** | PSOLA with no change | Separates our manipulation's effect from PSOLA's own artifacts |
| **±20 ms jitter test** | Shift boundaries randomly | Typical aligner error; the score must not depend on it |
| **Spearman / Kendall** | Rank correlation | Human ratings are ordinal (1–5), not interval |
| **Partial correlation on MOS** | Remove whole-sentence quality effect | Ensures SDS isn't just re-detecting bad audio |
| **Steiger's test** | Compares two correlations with the same human ratings | Standard test when both metrics are scored on identical data |
| **Bootstrap CIs** | Resample raters and clips | Gives uncertainty without distribution assumptions |
| **Krippendorff's α ≥ 0.5** | Rater agreement floor | Below that, the human labels are too noisy to test anything |
| **~500 clips, 5–8 raters** | Size of the human study | Enough for stable correlations and a Steiger test; affordable |
| **Pre-registration** | Write pass bars before testing | Prevents tuning the metric to the test results |
