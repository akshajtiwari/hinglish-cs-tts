# SwitchMOS

SwitchMOS predicts how natural a clip of synthetic speech sounds, like a MOS score. It is aimed at speech where
current predictors such as UTMOS do poorly: modern TTS, Indian languages, and code-switched speech
(for example Hindi mixed with English). It is trained on existing human ratings and has an extra part
that scores the points where the language switches.

This repository has the code for preparing the data, freezing the splits and scoring the baseline predictors.
The datasets are not included.

## Layout

```
src/switchmos/
  files.py              save JSON / CSV / text safely (write to a temp file, then rename), file hashes
  run_log.py            a manifest.json for every run (config, git commit, hardware, results)
  data/
    columns.py          the columns of the three common tables (ratings, pairs, votes) and row checks
    load_*.py           one loader per dataset: BVCC, SOMOS, MANGO, SpeechArenaBench, SpeechJudge
    build_tables.py     builds the common tables (parquet) from the raw datasets
    make_splits.py      freezes the train / val / test splits
  eval/metrics.py       SRCC, LCC, MSE and pairwise accuracy
scripts/
  step1_download/       download and check the datasets
  step2_baselines/      score the test clips with UTMOS, UTMOSv2, DistillMOS and SCOREQ and evaluate them
notebooks/              data exploration notebooks (outputs cleared)
model/                  IndicF5 fine-tuning on HiACC (see model/README.md)
tests/                  unittest checks (bootstrap checks additionally use numpy)
```

## Setup

Python 3.11 with pyenv and a virtual environment:

```bash
pyenv install 3.11.16
~/.pyenv/versions/3.11.16/bin/python -m venv .venv
source .venv/bin/activate
pip install -e ".[data]"          # add ",train" for the training packages
```

The baseline scorers need their own environment, because their package versions clash with the main one:

```bash
bash scripts/step2_baselines/setup_baselines_env.sh
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Step 1: data

The scripts in `scripts/step1_download/` download the datasets and check their checksums. The datasets
folder is expected to contain `speechjudge/`, `speecharena_hi_AB/`, `mango/`, `somos/somos.zip` and `bvcc/main/`.

```bash
# build the common tables: <datasets>/_harmonized/*.parquet
PYTHONPATH=src python -m switchmos.data.build_tables --root ~/projects/hinglish-cs-tts/datasets

# freeze the splits: <datasets>/_splits/<version>/*.parquet and manifest.json
PYTHONPATH=src python -m switchmos.data.make_splits --root ~/projects/hinglish-cs-tts/datasets
```

Both skip work that is already done; use `--force` to rebuild.

## Step 2: baselines

```bash
# check that UTMOS gives the published result on the BVCC test set
PYTHONPATH=src python scripts/step2_baselines/check_utmos_on_bvcc.py --bvcc <bvcc>/main --out <out>

# extract the test audio and write the test lists: <datasets>/_exam/
PYTHONPATH=src python scripts/step2_baselines/prepare_exam_audio.py --root ~/projects/hinglish-cs-tts/datasets

# score every test clip with the four baselines (one GPU each), then evaluate
bash scripts/step2_baselines/run_all_scorers.sh
```

UTMOSv2 is slow (its spectrograms are made on the CPU). To spread it over several GPUs, `split_remaining.py` splits the
files it has not scored yet into one list per GPU, each list is scored by its own `score_baselines.py` job, and
`finalize_utmosv2_parts.sh` merges the parts back (`merge_parts.py`) and runs the evaluation.
`audio_durations.py` reports the shortest and longest exam clips per dataset.

For failure analysis, `collect_failure_evidence.py` checks SAB votes against source metadata,
checks selected audio copies, and measures basic audio properties without changing recordings.
`analyze_judge_failures.py` checks saved preference results, compares judges on the same examples
with sentence-level bootstrap intervals, reports consistently weighted shortcuts, and selects
successful listening comparisons. Both scripts expose their input/output paths through `--help`.
These are exploratory checks of existing predictions; they do not train or select a replacement judge.

The shell scripts use the server paths `~/projects/hinglish-cs-tts`, `~/projects/switchmos_code` and
`~/projects/baselines-venv`; change them at the top of each script for another machine.
Long jobs can be stopped and started again: finished work is skipped.

## Data

Datasets are not included. Each dataset has its own licence; check it before use.
SpeechArenaBench is used only as test data.
