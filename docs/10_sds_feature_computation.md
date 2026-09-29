# 10 — How each SDS feature is computed (v1, 2026-09-29)

Companion to 04_switch_point_evaluation.md. 04 says *what* is measured and why; this doc says *how*.

## 10.1 Inputs and framing

- **Waveform:** mono, resampled to 16 kHz, low-passed at 8 kHz (bandwidth match between HiACC and 24 kHz TTS output), loudness-normalized.
- **Word intervals:** list of `(word, start_s, end_s)` from MMS forced alignment on the uroman-romanized transcript, mapped back to the original mixed-script words.
- **Language per word:** Devanagari → hi, Latin → en.
- **Boundaries:** every adjacent word pair. Different languages = **switch**; same language = **ordinary boundary**.
- **Frames:** 25 ms window, 10 ms hop (≈300 frames for a 3 s clip).

Notation below: A = outgoing word, B = incoming word, at one boundary.

## 10.2 Features

### 1. Pause
- Initial: `start(B) − end(A)` from the aligner.
- Refinement (aligners absorb silence into words): frames within ±150 ms of the boundary more than 35 dB below the clip's loudest frame count as silence.
- **Output:** `pause_ms`.

### 2. Speech rate
- Syllables per word from text:
  - Hindi: count independent vowels + consonants not followed by halant (्).
  - English: CMU pronouncing dictionary; fallback = count vowel groups.
- Pre-rate = syllables in last 1–2 words before the boundary ÷ their duration. Post-rate likewise after.
- Each divided by the clip's overall syllable rate.
- Cross-check: de Jong & Wempe (2009) acoustic syllable nuclei (intensity peaks in voiced regions), spelling-independent.
- **Output:** `pre_rate_ratio`, `post_rate_ratio`.

### 3. Lengthening of the switched word
- Expected duration = syllables(B) × speaker's mean syllable duration in the clip.
- **Output:** `lengthening = duration(B) / expected` (>1 = stretched).

### 4. Pitch (F0)
- Two trackers every 10 ms, 60–400 Hz: Praat (Parselmouth) and PENN.
- Keep a frame only if both agree within 50 cents (removes octave errors, which mimic pitch jumps).
- Convert to semitones relative to the speaker's median F0: `st = 12·log2(f0 / median_f0)`.
- **`f0_jump_st`**: median st of last 100 ms of voiced frames in A minus median of first 100 ms in B. If a word edge is unvoiced, use nearest voiced frames within 150 ms.
- **`f0_range_ratio`**: (90th − 10th percentile st of B) ÷ mean range of the surrounding matrix-language words.
- **`f0_slope_pre`**: linear-fit slope (st/s) over the last 200 ms of A.
- Missing (fully unvoiced word) → NaN, never 0.

### 5. Loudness
- Per-frame energy: `20·log10(RMS)`.
- **`energy_jump_db`**: mean of last 100 ms of A minus first 100 ms of B, voiced frames only.
- **`energy_word_db`**: mean of B minus clip mean.

### 6. Spectral jump (seam)
- 13 MFCCs per frame, drop c0 (overall level, already covered by energy).
- Average last 3 *speech* frames of A and first 3 *speech* frames of B (across any pause, not the silence itself).
- **`mcd_jump`**: mel-cepstral distance between the two averages: `(10/ln10)·sqrt(2·Σ(c_a − c_b)²)`.
- **`kl_jump`**: symmetric KL divergence between the two frames' normalized power spectra (best single predictor of audible joins in Stylianou & Syrdal 2001).

### 7. Contrast (within-utterance normalization)
- Every feature is computed at **every** boundary.
- For each switch: subtract the mean of the same feature over the clip's ordinary boundaries; with ≥3 ordinary boundaries, also divide by their standard deviation (z-score).
- Clips with no ordinary boundaries: no contrast; used for SDS-boundary and SDS-seam only.

### 8. Missing values
- Marked NaN. Distance to the reference is computed on available dimensions (Mahalanobis on the observed sub-vector).

## 10.3 Example output row

```
clip AD21007  boundary 3  लिए → late  (hi→en, mid-phrase)
pause_ms            42
pre_rate_ratio      0.86     # slowed 14% into the switch
post_rate_ratio     0.94
lengthening         1.21     # 'late' 21% longer than expected
f0_jump_st         +2.4
f0_range_ratio      1.35     # wider pitch on the English word
f0_slope_pre_st/s  +3.1
energy_jump_db     +1.8
mcd_jump            4.7
kl_jump             0.62
+ the same fields as contrasts against this clip's ordinary boundaries
```

(Values illustrative, not measured.)

## 10.4 Feature → score part

| Feature | SDS-switch (contrast) | SDS-boundary (absolute) | SDS-seam |
|---|---|---|---|
| pause_ms | ✓ | ✓ | |
| pre/post_rate_ratio | ✓ | ✓ | |
| lengthening | ✓ | ✓ | |
| f0_jump_st, f0_range_ratio, f0_slope_pre | ✓ | ✓ | ✓ (jump only) |
| energy_jump_db, energy_word_db | ✓ | ✓ | ✓ (jump only) |
| mcd_jump, kl_jump | | | ✓ |

## 10.5 Tools

| Step | Library |
|---|---|
| Alignment | torchaudio `MMS_FA` + `uroman` (or `ctc-forced-aligner --romanize --language hin`) |
| Pitch | `praat-parselmouth`, `penn` |
| MFCC, RMS | `librosa` |
| Syllables (English) | CMU dict via `nltk` or `g2p_en` |
| Everything else | `numpy`, `scipy` |

Runs on a laptop CPU at a few clips per second; no GPU needed.

## 10.6 Known failure modes to test in the pilot

- Aligner boundary error > 25 ms (hand-check 20 boundaries in Praat).
- Octave errors surviving the two-tracker agreement filter.
- Syllable counts wrong for English loanwords written in Devanagari or Hindi words written in Latin (HiACC is script-consistent, but TTS test text may not be).
- Very short clips (<3 words) with no ordinary boundary.
