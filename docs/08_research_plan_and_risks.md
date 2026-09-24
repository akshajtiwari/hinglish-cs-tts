# 08 — Research Plan and Risks (v1)

## 8.1 Phases

| # | Phase | Weeks | Output | Gate |
|---|---|---|---|---|
| 0 | **Read + resolve** | 1 | Dhoundiyal 2023 PDF read; Rao 2018 dataset downloaded; HiACC license email sent; IndicF5 gated access + vocab.txt inspected for Latin coverage | Latin coverage known; license answer or fallback to CC BY reading |
| 1 | **Data + alignment** | 2 | HiACC adult cleaned, MMS+uroman word alignments, 100 hand-checked boundaries with aligner error reported; switch inventory stratified by direction × boundary type × island length | Boundary error < 25 ms median; ≥800 usable natural switches |
| 2 | **Natural switch signature** | 1–2 | Feature extraction on HiACC + IIT-B natural switches; reference distributions; replicate Rao 2018 (slower/louder/higher-range English) on spontaneous data | Rao effect replicates (or the paper reports it does not, which is itself a finding) |
| 3 | **Baselines synthesized** | 1 | IndicF5 zero-shot, IndicF5 + char-count patch, Orato, Indic Parler, Kokoro (open); Bulbul v3, Gemini TTS (closed, for human eval) on HiACC test sentences + COMI-LINGUA sample + harrrshall 30 | All systems produce audio for the same ≥300 switch sentences |
| 4 | **SDS v1 + pilot validation** | 2 | Metric code; pilot: 50 switch windows × 3 raters; choose window/stratification variants | SDS-vs-rating Spearman > 0.4 on pilot, or redesign |
| 5 | **Fine-tune** | 2 | LoRA and full fine-tunes of IndicF5 on HiACC adult (+ clean-Hindi mix) under script policies A and B; checkpoint by validation SDS | Monolingual CER retention within 2 pts absolute of base |
| 6 | **Full human eval** | 2 | ≥500 switch windows, 5–8 bilingual raters, three tasks (rating, region highlighting, word-ID in noise), plus utterance MOS | Inter-rater agreement (Krippendorff α) > 0.5 on switch rating |
| 7 | **Analysis + ablations** | 2 | SDS vs human vs baseline metrics (join cost, PBD, CMI_speech, LID-conf, dur-abnormal, UTMOS, NISQA, IndicMOS); local–global dissociation; fine-tune ablations (data type, script, LoRA/full, adult+child); per-word duration misallocation | |
| 8 | **Write-up + release** | 2 | Paper, `sds/` package, rating set, checkpoint, demo page | |

Total ≈ 14–16 weeks part-time. Phases 2–3 and 4–5 can overlap.

## 8.2 Experiments that must appear

1. **Local–global dissociation.** Systems ranked by utterance MOS vs by switch-window rating; show the rankings differ and SDS tracks the latter.
2. **Metric bake-off.** Correlation and ROC of SDS vs every baseline metric against the same human data.
3. **Natural vs spliced.** SDS-seam separates natural HiACC switches from same-speaker spliced switches (AUC).
4. **Fine-tune effect.** SDS-prosody (under-marking) before/after; monolingual retention; UTMOS/CER as honest secondary numbers even if they drop.
5. **Data-type ablation.** 3 h spontaneous (HiACC) vs 3 h read Hindi+English vs 3 h synthetic CS (CS-FLEURS/UniCoM-style splicing) vs Orato-scale call data: which moves the switch signature?
6. **Script policy.** Devanagari-transliterated vs Latin English: intelligibility, switched-word duration ratio, SDS.
7. **Duration misallocation.** Switched-word duration / natural duration as a function of script and patch.
8. **Downstream utility (if time).** Synthetic Hinglish from base vs fine-tuned → Whisper LoRA → MER and Code-Switch Bigram Accuracy on HiACC test (mirrors Biswas 2025, Yeo 2026).

## 8.3 Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| SDS does not correlate with switch-local ratings | Medium | Pilot early (phase 4). If raw features fail, train a small learned scorer on the rating set and report it as a data contribution; the local–global dissociation and natural-signature results still stand |
| Raters cannot judge a 1.5 s excerpt reliably | Medium | Provide full-utterance context on demand; use region highlighting and behavioural word-ID as complementary tasks; screen raters |
| Aligner error swamps 300 ms windows | Medium | Multi-resolution windows; hand-check 100 boundaries; MFA adaptation per Pandey 2026 if MMS is > 25 ms |
| Fine-tune degrades quality (SEAME precedent) | High | Report it; LoRA + low LR + clean mix; the paper's claim is about the switch, not fidelity |
| HiACC too small / too noisy to move the model | Medium | Scale-up path MUCS Hi-En (90 h, CC BY-SA); the metric paper does not depend on the fine-tune succeeding |
| HiACC license is NC | Low impact | Academic use fine; no commercial demo |
| Latin absent from IndicF5 vocab | Medium | Script policy A (Devanagari) is the default; C (extend vocab) as ablation |
| Rao 2018 effect does not replicate on spontaneous HiACC | Low–Medium | Report; use HiACC's own distribution as reference; discuss rehearsed vs spontaneous |
| Reviewer: "join cost rebrand" | High | Headline calibration-to-human + normalization + validation; bake-off against raw join cost |
| Reviewer: "SEAME did this" | High | Cite up front; position (a) as measured case study, not first |
| Closed systems (Bulbul, Gemini) TOS forbid benchmarking | Low | Check TOS; human eval only; omit if forbidden |
| Reference-free metric gets gamed | Low (diagnostic use) | State scope; show pause-insertion is penalized by the divergence term |

## 8.4 Open questions carried from v0, now answered

| v0 question | Answer |
|---|---|
| Dhoundiyal 2023 overlap | Body inaccessible; abstract is an application paper. Read before citing for any method. Low overlap risk |
| Child speech | Exclude from main fine-tune; robustness ablation only |
| Force alignment | HiACC is segment-level only. Use MMS_FA + uroman (mixed script, lexicon-free); refine with code-mixed MFA if needed |
| Compute | 50–100 GPU-hours, single A100 |
| Raters | 5–8 screened bilinguals; AI4Bharat-scale pools exist if needed |
| License | HiACC CC BY (Zenodo) vs CC BY-NC (paper), email authors; IndicF5 MIT/CC BY over NC init, academic fine |
| Test set | HiACC speaker-independent test split + COMI-LINGUA sample + harrrshall 30 |

## 8.5 Immediate next actions

1. Email HiACC authors re license; download `Corpus.zip` (MD5 `dd6cc9354e1dee5e2f25bc5243df88ac`) and inspect `code_switched_labels.json`.
2. Accept IndicF5 gate; dump `vocab.txt`; check for `a–z`.
3. Download Rao et al. 2018 IIT-B code-switch dataset.
4. Obtain Dhoundiyal 2023 PDF (IEEE Xplore via institution).
5. Run MMS_FA + uroman on 20 HiACC files; hand-check 20 boundaries in Praat.
6. Write `sds/features.py` and compute the natural switch signature on the 20 files. Decide window design from that.
