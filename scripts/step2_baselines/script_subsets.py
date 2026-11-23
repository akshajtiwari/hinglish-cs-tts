"""Split SAB votes by the script of their sentence, for the code-mixed test of Paper A (prereg doc 21, section 7).

The old rule (is_mixed) puts Latin-only sentences, which are mostly Romanized Hinglish, with the Devanagari-only
ones. This writes two votes tables for paper_a_extra_analyses.py:
  <out>/votes_native_or_mixed.csv  votes on Devanagari-only and mixed-script sentences, with a True/False column
                                   mixed_script (run with --subset-column mixed_script)
  <out>/votes_latin_only.csv       votes on Latin-only sentences (run without a subset column)
and prints how many votes (all, and decided with audio) fall in each class.

Run from the project folder:
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python scripts/step2_baselines/script_subsets.py \\
      --votes docs/ledger/artifacts/failure_analysis_20261015/inputs/exam/votes_speecharena.csv \\
      --pairs docs/ledger/artifacts/failure_analysis_20261015/inputs/speecharena_pairs.parquet --out <folder>
"""
import argparse
from pathlib import Path

from analyze_judge_failures import read_csv, save_rows
from switchmos.data.load_speecharena import script_class


def split_votes(votes, transcripts):
    """{"native": [...], "mixed": [...], "latin": [...]} of vote rows; native and mixed rows get mixed_script."""
    classes = {"native": [], "mixed": [], "latin": []}
    for row in votes:
        kind = script_class(transcripts[row["sentence_id"]])
        assert kind != "none", f"sentence {row['sentence_id']} has no letters"
        row = dict(row)
        row["mixed_script"] = str(kind == "mixed")
        classes[kind].append(row)
    return classes


def main():
    parser = argparse.ArgumentParser(description="SAB votes split by sentence script.")
    parser.add_argument("--votes", type=Path, required=True)
    parser.add_argument("--pairs", type=Path, required=True, help="harmonized speecharena_pairs.parquet (transcripts)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    import pyarrow.parquet
    transcripts = {}
    for row in pyarrow.parquet.read_table(args.pairs, columns=["sentence_id", "transcript"]).to_pylist():
        transcripts[row["sentence_id"]] = row["transcript"]
    classes = split_votes(read_csv(args.votes), transcripts)
    args.out.mkdir(parents=True, exist_ok=True)
    save_rows(args.out / "votes_native_or_mixed.csv", classes["native"] + classes["mixed"])
    save_rows(args.out / "votes_latin_only.csv", classes["latin"])
    for kind, rows in classes.items():
        decided = 0
        for row in rows:
            if row["label"] in ("A", "B") and row["audio_status"] == "ok":
                decided += 1
        print(f"{kind}: {len(rows)} votes, {decided} decided with audio")


if __name__ == "__main__":
    main()
