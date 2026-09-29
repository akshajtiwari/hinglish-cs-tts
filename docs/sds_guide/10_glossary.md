# 10 — Glossary

| Term | Plain meaning |
|---|---|
| **Code-switching** | Changing language mid-conversation or mid-sentence |
| **Switch point** | The boundary between two adjacent words in different languages |
| **Ordinary boundary** | A boundary between two words in the same language |
| **Borrowing / loanword** | A foreign word used as part of the other language ("office" in Hindi) |
| **Matrix language** | The main language of the sentence (usually Hindi in Hinglish) |
| **Embedded language** | The language inserted into it (usually English) |
| **Direction** | Hindi→English or English→Hindi |
| **Island** | A stretch of consecutive embedded-language words |
| **Forced alignment** | Finding each known word's start and end time in audio |
| **MMS** | Meta's Massively Multilingual Speech model; its alignment head handles 1,100+ languages |
| **uroman** | Converts any script to Latin letters so MMS can align it |
| **F0 / pitch** | How high or low the voice is |
| **Semitone** | A log pitch unit; makes male and female voices comparable |
| **RMS / dB** | Loudness |
| **MFCC** | A compact description of the spectrum (voice colour) per frame |
| **Mel-cepstral distance (MCD)** | Distance between two MFCC vectors; big jump = possible seam |
| **Prosody** | Rhythm, pitch, loudness, and timing of speech |
| **Hyper-articulation** | Saying a word more carefully: longer, higher pitch |
| **Contrast** | A switch's feature minus the same feature at the clip's ordinary boundaries |
| **Reference distribution** | What natural switches' features look like, learned from REF speakers |
| **Reference pack** | The frozen file holding the reference distributions and everything else SDS needs |
| **Mahalanobis distance** | Distance from the centre of a distribution that accounts for how features vary together |
| **Percentile** | Share of natural switches that are closer to typical than this one |
| **In-range rate** | Share of switches inside the natural 90% range |
| **Under-marked / over-marked** | Too little / too much of the human switch signature |
| **Seam** | An audible join, like two recordings glued together |
| **Splice control** | A deliberately glued clip, used to test seam detection |
| **Join cost** | The 1990s unit-selection measure of discontinuity at joins; our main competitor |
| **One-class model** | A model trained only on normal examples that scores how abnormal new inputs are |
| **Calibration** | Whether real speech actually scores as typical |
| **AUC** | How well a score separates two classes; 0.5 = chance, 1.0 = perfect |
| **Spearman / Kendall** | Rank correlations |
| **Partial correlation** | Correlation after removing the effect of another variable |
| **Steiger's test** | Tests whether one correlation with the human ratings is significantly higher than another |
| **Krippendorff's α** | How much raters agree with each other |
| **MOS / CMOS / MUSHRA** | Standard listening-test formats (01 in main docs, 06 here) |
| **FT / REF / TEST speakers** | Our speaker-disjoint roles: fine-tune, reference, test |
| **Pre-registration** | Writing down tests and pass bars before seeing results |
| **SwitchMOS** | Working name for the language-independent, switch-aware naturalness predictor (13) |
| **SSL encoder** | A speech model pretrained without labels (wav2vec2, HuBERT, WavLM); turns audio into feature vectors |
| **Multilingual encoder** | An SSL encoder pretrained on many languages (mHuBERT-147, MMS, w2v-BERT 2.0) |
| **Bradley–Terry loss** | Trains a scorer so that the preferred clip in a pair gets the higher score |
| **Pairwise accuracy** | Share of human-judged pairs where the model prefers the same clip as the human |
| **Leave-one-language-out** | Train on all languages but one, test on the held-out one; proves language independence |
| **Held-out system** | A TTS system never seen in training, used only for testing |
| **SpeechArenaBench** | AI4Bharat's pairwise TTS preference dataset, 10 Indic languages, MIT |
| **SpeechJudge** | ICLR 2026 naturalness judge trained on pairwise preferences incl. Mandarin–English code-switching |
| **Weak supervision** | Learning per-switch scores from clip-level labels only |
