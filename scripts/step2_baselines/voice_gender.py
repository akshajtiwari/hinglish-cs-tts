"""Is the predictors' preference for one system tied to one voice? A first test with the voice gender of each SAB vote.

SAB used each system's default voice configuration and paired voices of the same gender (Anand et al., 2026). The raw
"gender" column, which build_tables stores as rater_gender, is that voice gender: half of the raters have both values.
So for every system with a male and a female voice, the two genders are two different voices. For each voice gender
this gives, per system: listener win rate, each predictor's mean score and its top-scored system.
If a predictor ranks the same system first under both genders, its preference is not tied to a single voice.

Run from the project folder:
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python scripts/step2_baselines/voice_gender.py \\
      --votes docs/ledger/artifacts/failure_analysis_20261015/inputs/exam/votes_speecharena.csv \\
      --harmonized-votes docs/server_mirror/hinglish-cs-tts/datasets/_harmonized/speecharena_votes.parquet \\
      --scores docs/ledger/artifacts/paper_a_revision_20261123/utmosv2_10runs/scores_mean \\
      --out docs/ledger/artifacts/paper_a_revision_20261123/final/voice_gender.json
"""
import argparse
from pathlib import Path

from analyze_judge_failures import JUDGES, read_csv
from switchmos import files


def per_gender(votes, gender_of, scores):
    """{gender: {system: {"clips", "listener_win", judge means...}, "top": {judge: system}}} on decided votes."""
    report = {}
    for gender in sorted(set(gender_of.values())):
        systems = {}
        for vote in votes:
            if gender_of[vote["vote_id"]] != gender:
                continue
            winner = vote["system_a"] if vote["label"] == "A" else vote["system_b"]
            for side in ["a", "b"]:
                block = systems.setdefault(vote["system_" + side], {"clips": 0, "wins": 0, "sums": dict.fromkeys(JUDGES, 0.0)})
                block["clips"] += 1
                block["wins"] += vote["system_" + side] == winner
                for judge in JUDGES:
                    block["sums"][judge] += scores[judge][vote["path_" + side]]
        result = {"systems": {}, "top": {}}
        for system, block in systems.items():
            entry = {"clips": block["clips"], "listener_win": block["wins"] / block["clips"]}
            for judge in JUDGES:
                entry[judge] = block["sums"][judge] / block["clips"]
            result["systems"][system] = entry
        for judge in JUDGES:
            result["top"][judge] = max(result["systems"], key=lambda s: result["systems"][s][judge])
        result["top"]["listeners"] = max(result["systems"], key=lambda s: result["systems"][s]["listener_win"])
        report[gender] = result
    return report


def main():
    parser = argparse.ArgumentParser(description="System preference split by voice gender.")
    parser.add_argument("--votes", type=Path, required=True)
    parser.add_argument("--harmonized-votes", type=Path, required=True, help="speecharena_votes.parquet (rater_gender)")
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    import pyarrow.parquet
    table = pyarrow.parquet.read_table(args.harmonized_votes, columns=["vote_id", "rater_id", "rater_gender"]).to_pylist()
    gender_of = {row["vote_id"]: row["rater_gender"] for row in table}
    raters = {}
    for row in table:
        raters.setdefault(row["rater_id"], set()).add(row["rater_gender"])
    votes = [v for v in read_csv(args.votes) if v["label"] in ("A", "B") and v["audio_status"] == "ok"]
    assert all(v["vote_id"] in gender_of for v in votes), "a decided vote has no gender value"
    scores = {}
    for judge in JUDGES:
        scores[judge] = {row["path"]: float(row["score"]) for row in read_csv(args.scores / (judge + ".csv"))}

    report = {"votes": len(votes),
              "raters_with_both_values": sum(len(values) > 1 for values in raters.values()),
              "raters": len(raters),
              "by_gender": per_gender(votes, {v["vote_id"]: gender_of[v["vote_id"]] for v in votes}, scores)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    files.save_json(args.out, report)
    print(f"{report['raters_with_both_values']} of {report['raters']} raters have both gender values")
    for gender, block in report["by_gender"].items():
        print(gender, "top:", block["top"])
        for system, entry in sorted(block["systems"].items()):
            print(f"  {system:20s} clips {entry['clips']:5d} win {100 * entry['listener_win']:5.1f}% "
                  + " ".join(f"{j} {entry[j]:.2f}" for j in JUDGES))


if __name__ == "__main__":
    main()
