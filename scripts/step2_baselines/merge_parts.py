"""Add the UTMOSv2 scores of the GPU parts (analysis/step2/scores_parts/part*/) to the main scores file.

Run once, after every part job has stopped:
    ~/projects/baselines-venv/bin/python scripts/step2_baselines/merge_parts.py ~/projects/hinglish-cs-tts

The lines are copied as text, so no number is reformatted. If a file appears twice, it stops without writing
anything. Each merged part file is renamed to <name>.merged, so it can never be merged twice.
"""
import sys
from pathlib import Path


def path_of(line):
    """The file path of a CSV line "path,value" (the value is after the last comma)."""
    last_comma = line.rfind(",")
    return line[:last_comma]


def merge(main_file, part_files):
    """Append the lines of the part files to main_file. Returns the number of lines added."""
    main_lines = main_file.read_text().splitlines()
    seen = set()
    for line in main_lines[1:]:          # [1:] skips the header line
        seen.add(path_of(line))

    new_lines = []
    for part_file in part_files:
        part_lines = part_file.read_text().splitlines()
        if len(main_lines) == 0 and len(part_lines) > 0:
            main_lines.append(part_lines[0])     # the main file was empty: take the header from the part
        for line in part_lines[1:]:
            path = path_of(line)
            if path in seen:
                print(f"{path} appears twice ({part_file}); nothing was written")
                sys.exit(1)
            seen.add(path)
            new_lines.append(line)

    if len(new_lines) > 0:
        tmp = main_file.with_name(main_file.name + ".tmp")
        tmp.write_text("\n".join(main_lines + new_lines) + "\n")
        tmp.replace(main_file)
    for part_file in part_files:
        part_file.rename(part_file.with_name(part_file.name + ".merged"))
    return len(new_lines)


def main():
    base = Path(sys.argv[1]).expanduser()
    scores = base / "analysis" / "step2" / "scores"
    parts_root = base / "analysis" / "step2" / "scores_parts"
    for name in ["utmosv2.csv", "utmosv2_errors.csv"]:
        part_files = []
        for folder in sorted(parts_root.glob("part*")):
            if (folder / name).exists():
                part_files.append(folder / name)
        added = merge(scores / name, part_files)
        print(f"{name}: added {added} lines from {len(part_files)} part files")


if __name__ == "__main__":
    main()
