# 11 — Switch-aware naturalness predictor (proposed direction, 2026-09-29)

## 11.1 Why this idea

A switch-only score is niche. People want one number that says how human a whole clip sounds, the way UTMOS does. A clip can be natural at the switch and robotic everywhere else, and the headline number must reflect that.

So the proposal: **a whole-clip naturalness predictor for Hinglish, UTMOS-style, that explicitly looks at language switches.** SDS is not dropped. Its alignment, switch detection, features, and controls become the switch branch of this model and the explanation of its output.

## 11.2 Novelty check (quick, not exhaustive)

- Existing MOS predictors: UTMOS/UTMOSv2, SQuId (Google, multilingual), APG-MOS, SAMOS, a conversational-speech naturalness predictor (2026), IndicMOS (Indian languages).
- **None found that is trained or evaluated on code-switched speech, or that treats switch points specially.**
- Confidence: moderate. A full literature search is required before committing (see 11.9).

## 11.2b Full novelty search results (2026-09-29)

| Claim | Verdict | Evidence |
|---|---|---|
| First naturalness predictor trained/evaluated on code-switched speech | **Done (Mandarin–English)** | **SpeechJudge** (ICLR 2026, https://arxiv.org/abs/2511.07931): 99K pairwise naturalness annotations incl. zh2mixed / en2mixed; Bradley–Terry reward model (72.7%) and generative judge (77.2%); per-setting accuracy (84.8% zh2mixed). Its raters for mixed clips were L2-English Chinese speakers; agreement was lowest on mixed clips |
| First predictor with an explicit switch-point branch | **Novel as far as searched** | No work pools features around language-switch points. Ingredients exist: aligned prosodic features in MOS prediction (Vioni, ICASSP 2023, https://arxiv.org/abs/2211.00342); localize-then-fuse with synthetic local corruptions (DAMOS 2026, https://arxiv.org/abs/2608.21176); frame-level MOS (Kuhlmann 2025); alignment-based artifact localization (XSQ-AST 2026) |
| First predictor trained on SpeechArenaBench / Indic pairwise preferences | **Novel** | The source paper's only predictor is XGBoost on human axis ratings (no audio). No HF models tagged with the dataset; one citing paper, which doesn't use it. Dataset public since 2026-04-30 and tagged `bradley-terry`, `code-mixing`: expect competition |

**Strongest threats and positioning**
1. **SpeechJudge.** Do not claim "first code-switched predictor". Claim: whole-clip predictors, including SpeechJudge-style Bradley–Terry models, miss switch-local problems; an explicit switch branch fixes that. Add **SpeechJudge-GRM zero-shot** (https://huggingface.co/RMSnow/SpeechJudge-GRM) and a SpeechJudge-style BTRM trained on the same Hindi data as baselines.
2. **Limits of reference-free metrics** (https://arxiv.org/abs/2609.13150): on defect-free commercial systems, predictors are near chance and clip duration is a confound. Report duration-only and length-matched baselines; stratify pairs by whether they contain defects (SpeechArenaBench's noise and hallucination ratings); expect the switch-branch gain to concentrate on code-mixed pairs that differ on intelligibility or expressiveness.
3. **DAMOS.** Makes "localize then fuse" not new. The contribution is *switch anchoring* plus switch-specific controls (splice, flatten, exaggerate), and native bilingual raters for an Indic pair.

**Motivation to cite:** Takagi et al. 2026 (https://arxiv.org/abs/2606.19951): MOS predictors are insensitive to prosodic errors humans penalize. LCG 2026: UTMOS drops on code-switched output that humans prefer. IndicMOS 2024: zero-shot predictors degrade on Indian languages.

**Other checked, not threats:** MOS-RMBench (no CS/Indic), PrefSQA (language coverage not visible), EmergentTTS-Eval (zero-shot LLM judge, foreign-phrase category), Yeo CMI_speech (language-ID index, not naturalness), VoiceMOS 2026 (no CS or Hindi track), IndicMOS (no code-mixing).

**Exposure note:** the public repo (github.com/akshajtiwari/hinglish-cs-tts) is indexed by search engines, including the working title and plan.

## 11.2c SpeechArenaBench code-mixed content (from the paper, Table 1)

- 4,164 of 5,357 benchmark sentences (78%) are code-mixed, across 10 languages. Types: Latin-script English insertions, transliterated English in native script, mixed script.
- Rankings change "only modestly" between code-mixed and normalized input (Gemini first in all). This concerns system rankings, not switch sensitivity, but is a caution for the switch-branch gain.
- **Exact Hindi count (2026-09-29, `model/scripts/10_count_speecharena_codemix.py`, stats in `docs/data/speecharena_hi_stats.json`):**

| Item | Value |
|---|---|
| Hindi pairs total | 16,694 (9,290 unique sentences, 242 raters, 7 systems) |
| **Code-mixed pairs** (≥1 Devanagari and ≥1 Latin word) | **4,035** (24%), 2,493 unique sentences, 198 raters |
| Devanagari-only pairs | 11,281 (may include English transliterated into Devanagari, so the mixed count is a lower bound) |
| Latin-only pairs | 1,378 |
| Latin words per mixed sentence | mean 7.4, range 1–35 |
| Mixed-pair appearances per system | 738 (IndicF5) to 1,309 (Gemini) |
| Preference labels | single system, "Tie / No Preference" (677), or two systems listed together (e.g. "Gemini 2.5 Pro TTS, Eleven Labs v3", 403) — label semantics must be checked before training |
| `fine_grained_eval` | per-clip 1–5 ratings on noise, liveliness, voice_quality, expressiveness, hallucinations, intelligibility, plus a free-text comment. Early examples look mostly 1 or 5, so the scale may be used near-binarily |

- **Verdict: 4,035 code-mixed pairs is well above the 1,000 threshold.** Sentences are genuine intra-sentential Hinglish (e.g. "पापा ने कहा कि नया laptop दिला देंगे, but on one condition कि मुझे exams में अच्छे marks लाने होंगे।"), often with multi-word English islands, which is exactly the switch variety the model needs.
- The per-axis ratings can serve as auxiliary training targets (multi-task heads), and give the defect stratification the Limits paper recommends.

## 11.3 The data that makes it possible: SpeechArenaBench

Released by AI4Bharat with *Preferences of a Voice-First Nation* (Interspeech 2026). Checked on 2026-09-29 via the HF API:

| Item | Value |
|---|---|
| Hub id | `ai4bharat/SpeechArenaBench` |
| License | MIT |
| Access | gated, automatic approval |
| Languages | bn, gu, hi, kn, ml, mr, or, ta, te, ur |
| Hindi split | `val`, **16,694 pairwise examples**, ~35 GB with audio |
| Hindi fields | `sentence`, `model_a`, `model_b`, `audio_a`, `audio_b`, `preference_model`, `fine_grained_eval`, `user_id`, `gender`, `language`, `academic_prompt_id` |
| Whole study | 120K+ pairwise judgments, ~1,900 native raters, 7 systems (Gemini 2.5 Pro TTS, GPT-4o-mini TTS, ElevenLabs v3, Sonic 3, Speech 2.8 HD, Bulbul v3, IndicF5), 6 perceptual dimensions |

**Unknown, verify first:** how many Hindi sentences are code-mixed (scan `sentence` for Latin-script words; the paper reports 4,164 code-mixed sentences across all languages); what `fine_grained_eval` contains.

## 11.4 Model design (v1 sketch)

```
audio + transcript
   ├─ Whole-clip branch:  pretrained SSL encoder (WavLM / wav2vec2) → attention pooling → clip embedding
   ├─ Switch branch:      MMS alignment → switch windows
   │                        ├─ SSL embeddings pooled in each switch window
   │                        └─ SDS features (pause, rate, lengthening, pitch, energy, spectral jump)
   │                      → attention over switches → switch embedding  (zero vector if no switches)
   └─ Head: concat → MLP → naturalness score
          + auxiliary heads: per-switch seam / under / over (from controls)
```

## 11.5 Training

| Stage | Data | Loss |
|---|---|---|
| 1. Switch-branch pretraining | Our controls (spliced, flattened, exaggerated) built from REF speakers; natural switches | Classification: natural vs each break type. Free labels, no raters |
| 2. Preference training | SpeechArenaBench Hindi pairs | Pairwise ranking loss (Bradley–Terry: P(A preferred) = σ(s_A − s_B)); rater ID as an embedding, as UTMOS does with listeners |
| 3. Optional calibration | Any absolute MOS data (e.g. our small study) | Clipped MSE to map scores onto a 1–5 scale |

## 11.6 The experiment that decides whether it's a contribution

| Model | Description |
|---|---|
| **A. UTMOS off-the-shelf** | Reference point |
| **A2. SpeechJudge-GRM zero-shot** | Strongest existing code-switch-aware judge |
| **A3. Duration-only** | Confound check (Limits paper) |
| **B. Same encoder, fine-tuned on the same Hindi pairs, no switch branch** | **The real baseline** |
| **C. B + switch branch** | The proposal |
| D. SDS alone | The interpretable metric |

Primary result: **C beats B on code-mixed pairs** (pairwise accuracy against held-out human preferences), with no loss on monolingual pairs.
- If C > B: switches measurably drive listener judgments, and modelling them is new.
- If C ≈ B: listeners' whole-clip preferences don't hinge on switches. A clean, publishable negative result.

## 11.7 Evaluation protocol

- **Split by system, not clip:** train on some TTS systems, test on held-out ones, or the model memorizes which system is best. Also hold out raters and sentences.
- **Metrics:** pairwise accuracy; Kendall τ of system rankings vs Bradley–Terry human rankings; system-level Spearman ρ.
- **Subsets:** code-mixed vs monolingual pairs, reported separately.
- **Second test set:** our own switch-focused listening study (sds_guide/06), with systems not in SpeechArenaBench (Orato, our fine-tune, Indic Parler).
- **Ablations:** switch branch with SSL embeddings only / SDS features only / both; with and without control pretraining.

## 11.8 Risks

| Risk | Mitigation |
|---|---|
| Few code-mixed Hindi pairs | Scan first (11.3); if thin, add other languages' code-mixed items or collect targeted pairs |
| 7 systems give little variety at switches | Add our controls as synthetic preference pairs (natural > spliced) |
| Leave-system-out with 7 systems is small | Report per-held-out-system results; add our systems as a second test set |
| Model learns system identity, not naturalness | System-held-out evaluation; check predictions within a single system |
| 35 GB download | Stream only Hindi shards; cache on the server (4.6 TB free) |
| Compute | SSL-encoder fine-tuning fits one 16 GB A16 with small batches; the 4×A16 server is enough |

## 11.9 How this changes the plan

- **SDS work stays and moves earlier:** alignment, features, and controls are prerequisites for the switch branch.
- **The paper's framing shifts** from "a switch metric" to "a switch-aware naturalness predictor for code-switched TTS, with an interpretable switch diagnostic". Decision D16 in sds_guide/09.
- **New first steps:** (1) full novelty search for code-switched MOS prediction; (2) accept the SpeechArenaBench gate and count code-mixed Hindi pairs; (3) read `fine_grained_eval`.
- The fine-tuned IndicF5 remains a case study and an extra test system.

## 11.10 Sources

- SpeechArenaBench: https://huggingface.co/datasets/ai4bharat/SpeechArenaBench
- Preferences of a Voice-First Nation: https://arxiv.org/abs/2604.21481
- SQuId: https://arxiv.org/pdf/2210.06324
- APG-MOS: https://arxiv.org/html/2504.20447
- SAMOS: https://arxiv.org/html/2411.11232
- Conversational Speech Naturalness Predictor: https://arxiv.org/pdf/2603.01467
- UTMOSv2 (VoiceMOS 2024 T05): https://arxiv.org/pdf/2409.09305
