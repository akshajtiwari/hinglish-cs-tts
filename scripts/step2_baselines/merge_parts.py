"""Append the per-GPU UTMOSv2 scores (scores_parts/part<i>/) to the main scores file, once.

    ~/projects/baselines-venv/bin/python scripts/step2_baselines/merge_parts.py ~/projects/hinglish-cs-tts

Run only after every part job is stopped. Copies the lines as text (no number reformatting), refuses
duplicates, writes the main file atomically, then renames each part file to *.merged so it is never merged twice.
"""
import sys
from pathlib import Path

base = Path(sys.argv[1]).expanduser()
scores = base / "analysis" / "step2" / "scores"
parts = sorted((base / "analysis" / "step2" / "scores_parts").glob("part*"))

for name in ["utmosv2.csv", "utmosv2_errors.csv"]:
    main_file = scores / name
    main_lines = main_file.read_text().splitlines()
    seen = set()
    for line in main_lines[1:]:
        seen.add(line.rsplit(",", 1)[0])
    new_lines = []
    merged_files = []
    for part in parts:
        part_file = part / name
        if not part_file.exists():
            continue
        for line in part_file.read_text().splitlines()[1:]:
            path = line.rsplit(",", 1)[0]
            if path in seen:
                sys.exit(f"duplicate {path} in {part_file}; nothing written")
            seen.add(path)
            new_lines.append(line)
        merged_files.append(part_file)
    tmp = main_file.with_name(main_file.name + ".tmp")
    tmp.write_text("\n".join(main_lines + new_lines) + "\n")
    tmp.replace(main_file)
    for part_file in merged_files:
        part_file.rename(part_file.with_name(part_file.name + ".merged"))
    print(f"{name}: added {len(new_lines)} lines from {len(merged_files)} parts; now {len(main_lines) - 1 + len(new_lines)} rows")
