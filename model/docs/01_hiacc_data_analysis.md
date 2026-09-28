# 01 — HiACC as it actually is (inspected 2026-09-28)

Downloaded `Corpus.zip` from Zenodo 15551669 (531,628,684 bytes, MD5 `dd6cc9354e1dee5e2f25bc5243df88ac`, matches). Unzipped to `data/Corpus/`. Inspection script: `model/scripts/00_inspect_hiacc.py`.

## Layout (real, differs slightly from readme.txt)

```
Corpus/
  readme.txt
  adult/
    annotations/code_switched_labels.json     3,318 items: {audio, transcription, label}
    audio/{train_split,val_split,test_split}/AD?????.wav
    metadata/sentence_stats.csv               per-clip stats (see below)
    metadata/speaker_info.csv                 PID,Gender,Age,L1
    transcription/combined_output_changed_{train,val,test}_output.txt   lines "ADxxxxx.wav, <text>"
  children/
    annotations/code_switched_labels.json     1,858 items: {audio_filepath, transcription, label}
    audio/{train_split,val_split,test_split}/CH?????.wav
    metadata/{sentence_stats.csv, speaker_info.csv}
    transcript/{train,val,test}_output.txt
```

Speaker ID = first 4 chars of the filename (AD09, CH03). Splits are speaker-disjoint.

## Audio

| Subset | Split | Clips | Hours | Mean s | Median s | Min s | Max s |
|---|---|---|---|---|---|---|---|
| adult | train | 2,322 | 2.23 | 3.46 | 2.95 | 0.39 | 20.04 |
| adult | val | 332 | 0.33 | 3.59 | 3.08 | 0.37 | 14.57 |
| adult | test | 664 | 0.65 | 3.54 | 3.03 | 0.39 | 16.00 |
| children | train | 1,300 | 1.46 | 4.04 | 3.64 | 0.52 | 12.55 |
| children | val | 186 | 0.20 | 3.90 | 3.30 | 0.75 | 11.53 |
| children | test | 372 | 0.39 | 3.82 | 3.42 | 0.74 | 10.00 |
| **total** | | **5,176** | **5.27** | | | | |

All 16 kHz, mono, 16-bit PCM. Clips are **short** (median ~3 s, ~10 words). 169 adult clips are under 1 s (0.04 h). Only 0.04 h is over 15 s.

## What is actually code-switched (adult)

| Category | Clips | Share | Hours |
|---|---|---|---|
| Mixed (≥1 English and ≥1 Hindi word) | 1,214 | 37% | **1.46** |
| Pure English | 1,390 | 42% | ~1.2 |
| Pure Hindi | 714 | 22% | ~0.6 |

- Switches: 3,569 total in adult (1,679 Hi→En, 1,890 En→Hi), across 1,214 clips.
- Utterance labels: none 2,110 / intra-sentential 1,095 / inter-sentential 113.
- Mean CMI 9.5 (low: many monolingual clips drag it down); mean 172 WPM.
- 24 speakers, 89–216 clips each.
- Many pure-English clips are the *prompt questions* being read (e.g. "So the question is what's your favourite festival?"), i.e. read, not spontaneous.

**Consequence for training:** the "3.22 h of spontaneous Hinglish" is really **1.46 h of mixed speech** plus 1.76 h of monolingual Hindi/English from the same speakers. The monolingual clips are still useful (same voices, same mic, Indian English) but the switch-bearing data is half what the headline suggests. Children add 1,092 intra-sentential clips but are noisier and slower; reserve for ablation.

## Transcripts

- Format: one line per clip, `ADxxxxx.wav, text`. Hindi in Devanagari, English in Latin. Verbatim, mostly no punctuation.
- Readme says "manually curated"; paper says Whisper-seeded then corrected. Spot checks look clean.
- **Token-level language tags are not in the JSON** (only utterance `label`). Derive per-token LID from script: Devanagari → Hindi, Latin → English. `sentence_stats.csv` gives per-clip counts and switch counts, which we can use to verify the derivation.
- Children `sentence_stats.csv` has some empty CMI cells; handle as NaN.

## Metadata columns (`sentence_stats.csv`)

`audio, sentence, total_words, num_english_words, num_hindi_words, CMI, duration_sec, WPM, speech_rate, code_switch_count, hi_to_en_switch, en_to_hi_switch` (children adds `path`).

## Decisions

1. **Train set v1 = adult train split, all 2,322 clips** (mixed + monolingual). Keeping monolingual clips teaches the voices and Indian-English pronunciation; dropping them leaves ~1 h, too little.
2. **Weight or oversample mixed clips** (e.g. 2× the 1,214 mixed) so switches are not a minority of frames. Ablation: mixed-only vs all.
3. **Drop clips < 0.8 s** (near-silent fragments) and cap at 20 s (none exceed).
4. **Val = adult val split; test = adult test split** (speaker-disjoint as shipped). Never train on test.
5. **Resample 16→24 kHz** for IndicF5 (band-limited above 8 kHz; accepted).
6. **Clean-data mixing:** add Hindi studio speech (Rasa Hindi or IndicVoices-R Hindi, gated CC BY) at roughly 1:1 hours to protect base quality. Decide after first run.
7. **Script policy A** (English in Latin, as transcribed) for v1 *if* IndicF5's vocab has Latin letters; otherwise transliterate English to Devanagari with IndicXlit. Check vocab first (see 02 recipe doc).
