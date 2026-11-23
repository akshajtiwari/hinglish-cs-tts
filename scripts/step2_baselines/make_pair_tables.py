"""Turn MANGO MUSHRA pages into a pairwise votes table, so paper_a_extra_analyses.py can split judge accuracy there.

On a MUSHRA page every system reads the same sentence and is rated side by side, so each two systems on a page make
one pair. The label is the system with the higher mean rating; equal means are left out and counted. One page is one
sentence, so the bootstrap in paper_a_extra_analyses.py resamples pages. There is no rater reference (only means).
docs/plan/21_paper_a_generalisation_prereg.md fixes what is used: Tamil, plain "mushra" variant, both test splits,
with all five systems and again without the anchor and the hidden reference.

Run from the project folder:
  PYTHONPATH=src:scripts/step2_baselines ~/.venvs/switchmos-analysis/bin/python \\
      scripts/step2_baselines/make_pair_tables.py \\
      --clips docs/server_mirror/hinglish-cs-tts/datasets/_exam/clips_mango.csv --lang ta --variant mushra \\
      [--drop-systems anchor,reference] --out <folder>/mango_pages_ta.csv
"""
import argparse
from pathlib import Path

from analyze_judge_failures import group_by, read_csv, save_rows

COLUMNS = ["vote_id", "pair_id", "path_a", "path_b", "label", "tie_kind", "system_a", "system_b", "mixed", "lang",
           "sentence_id", "rater_id", "audio_status"]


def page_pairs(clips, lang, variant, drop_systems):
    """Votes-format rows for every two systems on every page, and the number of pairs left out for equal means."""
    rows = []
    equal = 0
    chosen = []
    for clip in clips:
        if clip["lang"] == lang and clip["variant"] == variant and clip["system"] not in drop_systems:
            clip = dict(clip)
            clip["sentence"] = clip["audio_path"].rsplit("/", 1)[1]
            chosen.append(clip)
    for sentence, page in sorted(group_by(chosen, "sentence").items()):
        page = sorted(page, key=system_name)
        for i in range(len(page)):
            for j in range(i + 1, len(page)):
                a = page[i]
                b = page[j]
                if float(a["mos"]) == float(b["mos"]):
                    equal += 1
                    continue
                label = "A" if float(a["mos"]) > float(b["mos"]) else "B"
                status = "ok"
                if a["audio_status"] != "ok" or b["audio_status"] != "ok":
                    status = "missing"
                pair_id = f"mango:{lang}:{variant}:{sentence}:{a['system']}|{b['system']}"
                rows.append({"vote_id": pair_id, "pair_id": pair_id, "path_a": a["path"], "path_b": b["path"],
                             "label": label, "tie_kind": "", "system_a": a["system"], "system_b": b["system"],
                             "mixed": "False", "lang": lang, "sentence_id": sentence, "rater_id": pair_id,
                             "audio_status": status})
    return rows, equal


def system_name(clip):
    """Sort key: the clip's system name."""
    return clip["system"]


def main():
    parser = argparse.ArgumentParser(description="MANGO MUSHRA pages as a pairwise votes table.")
    parser.add_argument("--clips", type=Path, required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--variant", default="mushra")
    parser.add_argument("--drop-systems", default="", help="comma-separated systems to leave out")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    drop_systems = []
    if args.drop_systems:
        drop_systems = args.drop_systems.split(",")
    rows, equal = page_pairs(read_csv(args.clips), args.lang, args.variant, drop_systems)
    assert rows, "no pairs: check --lang and --variant"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    save_rows(args.out, rows)
    pages = len(group_by(rows, "sentence_id"))
    print(f"{args.out}: {len(rows)} pairs on {pages} pages, {equal} left out for equal means")


if __name__ == "__main__":
    main()
