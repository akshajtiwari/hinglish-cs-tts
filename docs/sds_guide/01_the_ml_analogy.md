# 01 — SDS as if it were an ML model

You already know the normal pipeline: collect labelled data, train a model, test it on held-out data, report accuracy, precision, recall, F1, then deploy it. SDS follows the same shape. The pieces just have different names.

## 1.1 The mapping

| Normal supervised model | SDS |
|---|---|
| **Task** | Given a clip, say how human-like each language switch is |
| **Training data** | Natural Hinglish speech from the **reference speakers** only. Plus, for the seam part, artificially spliced copies of that speech |
| **Labels** | Only one label: "this is natural". No human ratings are used in training |
| **Model type** | **One-class / anomaly-detection model.** It learns what normal looks like and scores how abnormal a new input is. Like fraud detection trained only on normal transactions |
| **Model parameters** | Per group: average feature values and how features vary together (mean vector + covariance matrix). Seam classifier weights. Percentile lookup tables |
| **Training procedure** | Averaging and counting (fitting Gaussians, one logistic regression). No gradient descent, no GPU |
| **Hyperparameters** | Window lengths, which features, how switches are grouped, the "in range" threshold. Chosen only on the reference speakers, never on test data |
| **Validation set** | Controls (spliced, flattened, exaggerated clips) built from reference speakers, held out by speaker fold |
| **Test set** | (a) natural speech from **test speakers**; (b) controls built from test speakers; (c) TTS clips rated by bilingual humans |
| **Test metrics** (accuracy / F1 / AUC) | See 1.2: calibration, control-detection AUC and F1, correlation with human ratings, head-to-head against join cost |
| **Inference** | Score any new audio + transcript with the frozen parameters |
| **Deployment** | Python package + frozen reference file, versioned |

## 1.2 What "accuracy" means for SDS

A metric is tested by how well it agrees with the truth. There are three kinds of truth, so three kinds of test numbers.

| Truth | Where it comes from | Test number | Like |
|---|---|---|---|
| **Known-good** | Natural speech from test speakers | Median percentile ≈ 50; ~90% of natural switches "in range" | Calibration / false-positive rate |
| **Known-bad** | Controls where we deliberately broke the switch | AUC, precision, recall, F1 for detecting each break type | Classification accuracy |
| **Human judgement** | Bilingual raters scoring switch clips | Spearman / Kendall correlation; beats raw join cost by Steiger's test | Regression R² against a gold label |

The last row is the one the paper stands on. The first two are cheap and come first; if they fail, there's no point paying raters.

## 1.3 Why no human ratings in training

- About 500 rated clips is enough to **test** a metric, not enough to also train one.
- Training on them would leave nothing independent to test on.
- Learned MOS predictors trained on one domain break on others (UTMOS agrees with humans at only 0.26 on Hindi).
- A one-class model built from natural speech can explain itself: "no slowdown, flat pitch". A regressor trained on ratings just outputs a number.

A learned version trained on ratings is a possible follow-up (SDS v2), once this rating set exists.

## 1.4 Where the fine-tuned TTS model fits

The fine-tuned IndicF5 is **not** part of SDS. It's one of the systems SDS will score. Think of it as one of the "test inputs", not part of the model. It's also a user of SDS: we use SDS to pick its best checkpoint.

| Thing | Trained on | Role |
|---|---|---|
| SDS reference | HiACC **reference speakers** (natural speech) | The metric's "model" |
| SDS seam classifier | Reference speakers: natural vs spliced | Part of the metric |
| Fine-tuned IndicF5 | HiACC **fine-tune speakers** | A system being measured |
| Human rating set | Raters listening to TTS clips from **test** sentences | Test labels for the metric |

No speaker appears in more than one of these rows. That is what prevents the fine-tune from scoring well just by imitating the reference.
