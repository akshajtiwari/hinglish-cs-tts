# 16 — Glossary

| Term | Plain meaning |
|---|---|
| **Code-switching** | Changing language inside a conversation or sentence |
| **Switch** | The boundary between two adjacent words in different languages |
| **Ordinary boundary** | A boundary between two words in the same language |
| **Loanword** | A foreign word used as part of the other language ("office" in Hindi) |
| **TTS** | Text-to-speech |
| **MOS** | Mean Opinion Score: people rate clips 1–5 |
| **MOS predictor** | A neural network that guesses the MOS (UTMOS, DNSMOS, …) |
| **UTMOS / UTMOSv2** | The best-known MOS predictors (2022 / 2024) |
| **SpeechJudge** | A 7B preference-trained naturalness judge (ICLR 2026) that includes Mandarin–English code-switching |
| **SpeechArenaBench** | AI4Bharat's pairwise TTS preference dataset in 10 Indian languages |
| **Pairwise preference** | A rater hears A and B and says which is better (or tie) |
| **Bradley–Terry** | A model/loss where the better clip should get the higher score |
| **Davidson ties** | An extension of Bradley–Terry that uses ties instead of discarding them |
| **Pairwise accuracy** | How often the model picks the same clip as the human |
| **SSL encoder** | A speech model pretrained on unlabelled audio that turns sound into feature vectors |
| **Multilingual encoder** | An SSL encoder trained on many languages (mHuBERT-147, XLS-R, MMS) |
| **Expert** | A sub-model specialised in one view (whole clip, switches, artefacts) |
| **Gate** | A small network that decides how much each expert counts |
| **Soft-minimum** | A smooth "worst of" over switch scores, so one bad switch lowers the clip score |
| **Minimal pair** | Two versions of the same clip that differ only in one small region |
| **Speech editing / infilling** | Regenerating only part of a clip with TTS, keeping the rest |
| **Vocoder** | Turns a spectrogram into a waveform |
| **Resynthesis** | Passing audio through a vocoder without changing it (used as a fair control) |
| **SwitchLM** | Our small label-free model of what natural switches sound like |
| **Surprisal** | How unexpected something is to a model (high = unusual) |
| **Forced alignment** | Finding each known word's start and end time in audio |
| **MMS / uroman** | Meta's multilingual aligner / a tool that romanizes any script so MMS can read it |
| **F0 / pitch** | How high or low the voice is |
| **Semitone** | Log pitch unit; makes voices comparable |
| **Seam** | An audible join, like two recordings glued together |
| **Under- / over-marked** | Too little / too much of the natural switch signature |
| **Held-out system / language** | A TTS system or language kept out of training and used only to test |
| **Leave-one-language-out** | Train on all languages but one; test on that one |
| **Active learning** | Choosing which clips humans should rate, where the model is least sure |
| **Krippendorff's α** | How much human raters agree with each other |
| **AUC** | How well a score separates two classes (0.5 chance, 1 perfect) |
| **Spearman / Kendall** | Rank correlations |
| **16 kHz / 8 kHz** | Sampling rate / cutoff frequency; HiACC is 16 kHz, so everything is matched to it |
| **Switch point** | The boundary between two adjacent words in different languages |
| **Borrowing / loanword** | A foreign word used as part of the other language ("office" in Hindi) |
| **MMS** | Meta's Massively Multilingual Speech model; its alignment head handles 1,100+ languages |
| **uroman** | Converts any script to Latin letters so MMS can align it |
| **RMS / dB** | Loudness |
| **MFCC** | A compact description of the spectrum (voice colour) per frame |
| **Mel-cepstral distance (MCD)** | Distance between two MFCC vectors; big jump = possible seam |
| **Under-marked / over-marked** | Too little / too much of the human switch signature |
| **Join cost** | The 1990s unit-selection measure of discontinuity at joins; our main competitor |
| **MUSHRA** | Listening test scoring several versions 0–100 against a hidden reference and a bad anchor |
| **CMOS** | Comparative MOS: how much better B is than A, −3 to +3 |
| **Matrix / embedded language** | The main language of a sentence / the language inserted into it |
| **Prosody** | Rhythm, pitch, loudness, and timing of speech |
| **Hyper-articulation** | Saying a word more carefully: longer, higher pitch |
| **Contrast (switch features)** | A switch's feature minus the same feature at the clip's ordinary boundaries |
| **Local event** | A brief moment that can sound wrong: a switch, a join, a name, a number |
| **Local-event branch** | The part of SwitchMOS that scores local events |
| **Dataset / rater embedding** | Learned tags telling the model which dataset or listener a label came from |
| **Stacking / ensembling** | Combining several models' predictions; small gains in UTMOS |
| **Pre-registration** | Writing tests and pass bars down before seeing results |
| **Steiger's test** | Tests whether one correlation with the same human ratings beats another |
| **Vendor terms of service (ToS)** | Rules from TTS companies on how their generated audio may be used |
| **Cut-list** | Pre-agreed features to drop, in order, if the schedule slips |
