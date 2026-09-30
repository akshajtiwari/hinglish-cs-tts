# 07 — Evaluation: proving it beats UTMOS where it matters

Every test uses data not seen in training. Pass bars are fixed before any result is seen.

## 7.1 Evaluation suite

| Group | Sets | Metrics | Why |
|---|---|---|---|
| **Modern pairwise** (headline) | SpeechJudge-Eval; MOS-RMBench; a clean commercial TTS set (TTS-HP protocol) | Pairwise accuracy, with human ceiling and longest-clip heuristic; small-difference pairs reported separately | Where UTMOS/UTMOSv2 are near chance |
| **Indic** (headline) | SpeechArenaBench held-out systems and held-out languages; MANGO held-out systems | Pairwise accuracy; system-ranking Kendall τ; MUSHRA SRCC | Where off-the-shelf predictors fail |
| **Code-switched** (headline) | SpeechArenaBench code-mixed vs monolingual subsets; SpeechJudge mixed slice | Pairwise accuracy per subset | The specific gap we target |
| **Classic** (no-harm) | BVCC utt/sys; SOMOS; VMC'23 tracks; VMC'24 T1 zoomed; BC2019 Mandarin | SRCC, LCC, MSE | Must stay competitive with UTMOS/UTMOSv2 |
| **Local events** | Held-out edited pairs with known locations; our human switch study (08) | Localization AUC; correlation with human switch ratings | Per-event scores mean something |
| **Out-of-domain probes** | Conversational, emotional (VMC'26), long-form | Correlation / accuracy | Generalization |
| **Robustness** | Loudness, sample rate, ±20 ms alignment jitter; reward-hacking test | Stability; held-out metric after optimizing a TTS against it | Safe to use as a reward |

## 7.2 Baselines

UTMOS · UTMOSv2 · DNSMOS · APG-MOS / DistilMOS (if checkpoints exist) · SpeechJudge-GRM (4-bit, 7B) · longest-clip heuristic · **our model without the local-event branch** · our model trained on UTMOS's data only (to separate data from architecture).

## 7.3 Pre-registered success criteria

1. **Headline:** beat UTMOSv2 on modern pairwise, Indic, and code-switched sets (paired bootstrap, p < 0.05).
2. **No harm:** within a small margin of UTMOSv2 on classic sets.
3. **Local-event branch:** significant gain on code-switched subsets, no loss on monolingual.
4. **Versus SpeechJudge:** match BTRM (72.7%) on SpeechJudge-Eval at 10–25× smaller size (GRM's 77.2% is a stretch goal).
5. **Per-event validity:** localization AUC ≥ 0.8; positive, significant correlation with human switch ratings.

## 7.4 Claims ranked by expected strength

| Claim | Expected |
|---|---|
| Beats UTMOS/UTMOSv2 on Indic and code-switched pairs | High (partly from in-domain data; the data-only ablation separates this) |
| Beats UTMOS/UTMOSv2 on modern pairwise sets | Fairly high (SpeechJudge-Data in the mix) |
| Competitive on classic sets | Fairly high |
| Local-event branch helps on code-switched pairs | Uncertain (DAMOS-style gains can be small) |
| Matches SpeechJudge-BTRM | Uncertain |
| Generalizes to held-out languages | Unknown until data is counted |

## 7.5 Possible outcomes

| Outcome | Meaning |
|---|---|
| All pass | A better whole-clip predictor for modern and multilingual speech, with per-event explanations |
| Whole-clip wins, local branch doesn't help | Data and objectives drive the win; switch scores remain a diagnostic |
| Local branch helps only on code-switched subsets | Expected and fine: it's a specialist component |
| Fails on held-out languages | Claim narrows to trained languages |
