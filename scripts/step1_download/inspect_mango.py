"""Read-only look at the MANGO download. Run inside the hinglishtts venv, from datasets/mango.

Prints the rows and distinct raters per CSV, the columns, and the audio sample rate,
channels and duration per language. Audio files live at audios/<Language>/<System>/*.wav.
"""
import csv
import glob

import soundfile

rows = []
for path in sorted(glob.glob("csvs/*.csv")):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    raters = set()
    for row in rows:
        raters.add(row.get("Rater_ID"))
    print(path, len(rows), "raters", len(raters))

# columns and an example row, from the last CSV read above
first_row = rows[0]
print("cols", list(first_row.keys()))
example = {}
for key in list(first_row)[:12]:
    example[key] = first_row[key]
print("example", example)

wav_paths = glob.glob("audios/*/*/*.wav")
formats = {}
durations = {}
systems = set()
for path in wav_paths:
    info = soundfile.info(path)
    parts = path.split("/")
    lang = parts[1]
    systems.add(parts[2])
    key = (lang, info.samplerate, info.channels)
    formats[key] = formats.get(key, 0) + 1
    if lang not in durations:
        durations[lang] = []
    durations[lang].append(info.duration)

print(formats)
for lang, values in durations.items():
    mean = sum(values) / len(values)
    print(lang, len(values), f"dur min/mean/max {min(values):.1f}/{mean:.1f}/{max(values):.1f}")
print(sorted(systems))
