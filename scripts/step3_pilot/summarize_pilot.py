"""Step 3 pilot, part 4: compare the encoders on validation and name the winner (the pre-registered rule).

Reads <analysis>/pilot_<encoder>_seed<seed>/summary.json for every encoder and seed, and picks the encoder with the
highest mean selection score over its seeds (docs/plan/20_evaluation_spec.md). Validation numbers only.
Writes <analysis>/pilot_choice.json.

Run: PYTHONPATH=src python scripts/step3_pilot/summarize_pilot.py --analysis ~/projects/hinglish-cs-tts/analysis/step3
"""
import argparse
import json
from pathlib import Path

from switchmos import files
from switchmos import pilot

ENCODERS = ["xlsr", "mhubert", "w2vbert"]


def main():
    parser = argparse.ArgumentParser(description="Compare the pilot encoders on validation.")
    parser.add_argument("--analysis", required=True, help="the folder holding the pilot_<encoder>_seed<k> runs")
    args = parser.parse_args()
    analysis = Path(args.analysis).expanduser()

    table = {}
    for encoder in ENCODERS:
        runs = []
        for summary_path in sorted(analysis.glob(f"pilot_{encoder}_seed*/summary.json")):
            summary = json.loads(summary_path.read_text())
            runs.append(summary["best"])
        if len(runs) == 0:
            continue
        entry = {"seeds": len(runs)}
        for name in pilot.SELECTION_METRICS + ["selection"]:
            values = [run[name] for run in runs]
            entry[name] = sum(values) / len(values)
        table[encoder] = entry

    winner = None
    for encoder in table:
        if winner is None or table[encoder]["selection"] > table[winner]["selection"]:
            winner = encoder
    print(f"{'encoder':10} {'seeds':>5} {'selection':>9} {'SJ acc':>7} {'BVCC':>7} {'SOMOS':>7} {'MANGO':>7}")
    for encoder, entry in table.items():
        print(f"{encoder:10} {entry['seeds']:>5} {entry['selection']:>9.4f} {entry['speechjudge_val_accuracy']:>7.4f} "
              f"{entry['bvcc_val_srcc']:>7.4f} {entry['somos_val_srcc']:>7.4f} {entry['mango_val_srcc']:>7.4f}")
    print(f"winner: {winner}")
    files.save_json(analysis / "pilot_choice.json", {"winner": winner, "table": table})


if __name__ == "__main__":
    main()
