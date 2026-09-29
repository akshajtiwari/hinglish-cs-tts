# 04 — Switch features: the interpretable layer

This layer finds every switch and measures it with hand-designed features. It feeds the model (05) and produces the plain-language explanation. It needs no human labels.

## 4.1 Pipeline

1. **Normalize audio:** resample to 16 kHz, low-pass at 8 kHz, normalize loudness. (HiACC is 16 kHz phone audio; TTS is 24 kHz. Matching bandwidth stops features from detecting "synthetic" by bandwidth alone.)
2. **Tag words:** split transcript; language per word from script (or tagger, 03 §3.5).
3. **Align:** romanize with uroman; MMS forced alignment gives each word's start and end. Drop low-confidence words.
4. **Boundaries:** each adjacent word pair is a **switch** (languages differ) or **ordinary**. Record direction (Hi→En / En→Hi) and position (phrase boundary if pause ≥150 ms or punctuation).
5. **Features** at every boundary (25 ms frames, 10 ms hop):

| Feature | How |
|---|---|
| Pause | Gap between words, refined by frames >35 dB below peak within ±150 ms |
| Rate before / after | Syllables per second in 1–2 words each side ÷ clip rate |
| Lengthening | Incoming word duration ÷ (syllables × speaker's mean syllable duration) |
| Pitch jump | Median semitones, last 100 ms before vs first 100 ms after; two trackers (Praat, PENN) must agree within 50 cents |
| Pitch range / slope | Range of the switched word vs surrounding words; slope over 200 ms before |
| Loudness jump | dB, last 100 ms vs first 100 ms, voiced frames |
| Spectral jump | Mel-cepstral distance and symmetric KL between the 3 speech frames each side |

6. **Contrast:** each switch's features minus the clip's ordinary-boundary features (removes speaker, mic, and style).
7. **Compare with natural speech:** distance to the distribution of natural switches (REF speakers), as a percentile (50 = typical human), plus under- / over-marked flags and a seam probability.

## 4.2 The go/no-go check

Before relying on these features: on natural HiACC speech, do switches actually differ from ordinary boundaries as phonetics predicts (slowdown before, lengthening, wider pitch range)? Pre-registered pass: at least two of these effects, consistent across speakers. If not, the hand-crafted features are dropped and the switch expert relies on learned embeddings only.

## 4.3 Controls (built from natural speech)

| Control | How | Tests |
|---|---|---|
| Spliced | Same-speaker Hindi and English segments joined, 10 ms crossfade | Seam detection |
| Under-marked | Slowdown, lengthening, pitch bump flattened (Praat PSOLA) | Detects "robotic" switches |
| Over-marked | Inserted 300 ms pause or pitch reset | Detects exaggeration |
| Resynthesis-only | PSOLA with no change | Separates tool artefacts from real effects |

These controls also become cheap training pairs for the switch expert (06).

## 4.4 Tools

torchaudio `MMS_FA` + `uroman`, `praat-parselmouth`, `penn`, `librosa`, `numpy`/`scipy`. CPU only; a few clips per second.
