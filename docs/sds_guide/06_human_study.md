# 06 — The human study

## 6.1 Purpose

To produce the "gold labels" SDS is tested against (05, T3). Listeners judge **the switch moment**, not the whole sentence.

## 6.2 Stimuli

| Item | Plan |
|---|---|
| Sentences | ~70 HiACC TEST-speaker transcripts with ≥1 switch, plus ~30 COMI-LINGUA sentences for vocabulary breadth |
| Systems | Natural recording (where it exists), IndicF5 raw, IndicF5 + duration patch, Orato, Indic Parler, our fine-tune, Sarvam Bulbul, Gemini TTS; plus spliced controls |
| Voice | Every TTS system clones the same reference clip per sentence (a TEST speaker's clip) |
| Clips | ~1.5 s excerpt centred on one switch, 50 ms fades; full sentence available on click |
| Total | ~500 switch excerpts, stratified so each system and each direction is represented |

## 6.3 Tasks per rater

1. **Switch naturalness:** "How natural does the change of language sound?" 1 (clearly artificial) – 5 (completely natural).
2. **Region marking:** on the full sentence, click where it sounds wrong (if anywhere).
3. **Word identification in noise** (subset): hear the sentence with background noise, type the first word after the switch.
4. **Whole-sentence MOS** (subset): for the local-vs-global comparison.

## 6.4 Raters

- 5–8 fluent Hindi–English bilinguals, screened with a short hearing and attention check.
- Headphones required.
- Paid fairly; consent form; no personal data stored.
- Each rater hears every excerpt once, in randomized order; repeated items (~5%) to measure consistency.

## 6.5 Pilot first

- 50 excerpts, 3 raters.
- Check: instructions understood, α not near zero, no ceiling (everything rated 5).
- Adjust instructions or excerpt length, then run the full study.

## 6.6 Tools

webMUSHRA (browser) or a simple Gradio form; results stored as CSV: rater, clip, task, response, time.

## 6.7 Released artifact

The rated excerpts + anonymized ratings, so anyone can test their own metric against the same gold labels.

## 6.8 Role under SwitchMOS (update 2026-09-29)

SpeechArenaBench supplies the training labels, so this study is no longer the only human data. It becomes the **test of the per-switch scores**, which no public dataset labels. It also adds systems absent from SpeechArenaBench (Orato, our fine-tune, Indic Parler) as out-of-distribution test systems.
