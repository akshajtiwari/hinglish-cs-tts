# 04 — Building the core ("training" SDS)

This is everything that happens before SDS is frozen. Nothing here uses human ratings or test speakers.

## 4.1 Data roles and the speaker re-split

**Finding (2026-09-29):** HiACC's shipped adult train/val/test splits all contain the same 24 speakers. They split *utterances*, not speakers. So we define our own speaker-disjoint split and never use the shipped one.

Rules:
- Every speaker belongs to exactly one role.
- Each role is gender-balanced as far as possible and has enough switches.
- `AD63` has audio but no metadata row; `speaker_info.csv` lists `AD65` (F, 35) with no audio. Treated as the same female speaker.

Proposed split (all counts from `sentence_stats.csv`):

| Role | Speakers | F / M | Minutes | Switches | Used for |
|---|---|---|---|---|---|
| **FT** — fine-tune | AD36, AD09, AD63, AD47, AD35, AD43, AD21, AD30, AD26, AD42, AD27, AD23 | 4 / 8 | ~96 | ~1,695 | Training IndicF5 only |
| **REF** — reference | AD40, AD31, AD16, AD13, AD41, AD22 | 3 / 3 | ~45 | ~970 | Building SDS: reference distributions, seam classifier, hyperparameters |
| **TEST** — test | AD59, AD15, AD60, AD34, AD28, AD25 | 3 / 3 | ~51 | ~904 | Natural test speech, test controls, TTS test sentences and reference voices |

Machine-readable: `model/configs/hiacc_speaker_split.json`.

Cost of doing it right: the fine-tune gets ~1.6 h instead of ~2.2 h. Acceptable, and fixable later by cross-fitting (swap FT and REF, fit twice, average), which is an optional robustness check, not v1.

Other data:
| Data | Role |
|---|---|
| HiACC children | Not used in v1. Optional robustness check |
| IIT-B code-switch speech (Rao 2018) | Alternative reference pack for the robustness test |
| TTS outputs | Only ever scored, never used to build SDS |

## 4.2 Steps, in order

### Step B1 — Alignment pilot (REF speakers, 20 clips)
- Run MMS + uroman alignment.
- Hand-label 20 switch boundaries in Praat.
- **Done when:** median boundary error is measured. If >25 ms, adapt an MFA model before going on.

### Step B2 — Extract features on all REF speech
- Every boundary in every REF clip → one row.
- Drop boundaries with low alignment confidence; mark pitch NaN where trackers disagree.
- **Output:** `ref_boundaries.parquet`.

### Step B3 — The natural-signature gate (the go/no-go)
- Per speaker, compare switch boundaries with ordinary boundaries (paired, then combined across the 6 speakers).
- Expected from the literature: pre-switch slowing, lengthening of the switched word, wider pitch range on it, possibly louder embedded English.
- **Pass:** at least two of these effects in the predicted direction and consistent across most speakers.
- **Fail:** stop and rethink. Either the features are wrong or HiACC's switches don't carry the signature, and the paper's premise needs to change.

### Step B4 — Fix the design choices (hyperparameters)
Chosen by leave-one-speaker-out within REF, using how well each option separates natural from the dev controls (Step B6), never by test data:
- Window lengths (syllable-anchored vs fixed 150/300 ms).
- Grouping: direction × position (4 groups) vs direction only (2 groups). Default to 2 if any group has <100 switches.
- Feature set: drop any feature that is too noisy (e.g. high NaN rate).
- **Output:** `config.yaml`, frozen.

### Step B5 — Fit the reference distributions
- For each group: mean vector and covariance of switch contrasts, with Ledoit–Wolf shrinkage (stable with few samples).
- Same for ordinary boundaries (absolute features).
- **Marking direction:** the average natural contrast vector, normalized. Projection onto it says whether a switch is under- or over-marked.
- **Percentile tables:** distances of natural REF switches to their group, each computed with that speaker left out, so the table reflects unseen natural speakers.

### Step B6 — Build dev controls and fit the seam classifier
From REF speakers only:
- **Spliced:** same speaker, a Hindi segment and an English segment from different clips joined at a switch with a 10 ms crossfade.
- **Under-marked:** natural switch with slowdown, lengthening, and pitch bump flattened (Praat PSOLA).
- **Over-marked:** natural switch with an inserted 300 ms pause or a pitch reset.
- **Resynthesis-only:** passed through PSOLA unchanged.
- Seam classifier: logistic regression, natural vs spliced, on jump features. Cross-validated by speaker.

### Step B7 — Unit tests on the core
- Determinism; loudness and sample-rate invariance; ±20 ms jitter stability; NaN handling; clips with no ordinary boundaries.

### Step B8 — Freeze
- Save the reference pack (`hinglish-v1`): config, group parameters, percentile tables, seam weights, aligner and uroman versions, speaker lists.
- Tag the code in git.
- Write down the test plan and pass bars (05) **before** looking at any test result.

**After B8, nothing in the core changes.** If testing reveals a problem, that becomes `hinglish-v2` and is re-tested from scratch.
