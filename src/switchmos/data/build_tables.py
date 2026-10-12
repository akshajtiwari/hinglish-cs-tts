"""Build the common tables (parquet files) from the raw datasets.

    PYTHONPATH=src python -m switchmos.data.build_tables --root ~/projects/hinglish-cs-tts/datasets [--only mango,somos] [--force]

Writes <root>/_harmonized/<dataset>_<ratings|pairs|votes>.parquet, checks every row against columns.py,
logs to <root>/_harmonized/build.log and saves the row counts in counts.json.
Tables that already exist are skipped unless --force is given. The raw datasets are only read.
"""
import argparse
import time
from pathlib import Path

from switchmos.data import columns
from switchmos.data import load_bvcc
from switchmos.data import load_mango
from switchmos.data import load_somos
from switchmos.data import load_speecharena
from switchmos.data import load_speechjudge
from switchmos.files import load_json
from switchmos.files import save_json

DATASETS = ["speechjudge", "speecharena", "mango", "somos", "bvcc"]
TABLE_KINDS = {
    "speechjudge": ["pairs", "votes"],
    "speecharena": ["pairs", "votes"],
    "mango": ["ratings"],
    "somos": ["ratings"],
    "bvcc": ["ratings"],
}
# known row counts; a different count is reported in the log
EXPECTED = {
    "speechjudge_pairs": 99369,
    "speecharena_pairs": 2364,
    "speecharena_votes": 4444,
    "mango_ratings": 269150,
}


def log(message, log_file):
    """Print a message with the time and append it to the log file."""
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}"
    print(line, flush=True)
    log_file.write(line + "\n")
    log_file.flush()


def load_dataset(name, root):
    """Load one dataset and return a dict: table kind -> list of rows."""
    if name == "speechjudge":
        pairs, votes = load_speechjudge.load(root / "speechjudge")
        return {"pairs": pairs, "votes": votes}
    if name == "speecharena":
        pairs, votes = load_speecharena.load(root / "speecharena_hi_AB")
        return {"pairs": pairs, "votes": votes}
    if name == "mango":
        return {"ratings": load_mango.load(root / "mango")}
    if name == "somos":
        return {"ratings": load_somos.load(root / "somos" / "somos.zip")}
    if name == "bvcc":
        return {"ratings": load_bvcc.load(root / "bvcc" / "main")}
    raise ValueError(f"unknown dataset {name!r}")


def table_columns(kind):
    """The column definitions and the row check for one table kind."""
    if kind == "ratings":
        return columns.RATINGS_COLUMNS, columns.validate_rating
    if kind == "pairs":
        return columns.PAIRS_COLUMNS, columns.validate_pair
    if kind == "votes":
        return columns.VOTES_COLUMNS, columns.validate_vote
    raise ValueError(f"unknown table kind {kind!r}")


def count_invalid(rows, validator, table_name, log_file):
    """Count the rows with problems and log the first five."""
    bad = 0
    for row in rows:
        errors = validator(row)
        if errors:
            bad += 1
            if bad <= 5:
                log(f"  INVALID {table_name}: {errors[:3]}", log_file)
    return bad


def write_parquet(rows, column_types, path):
    """Write rows to a parquet file with fixed column types, atomically."""
    # pyarrow (not pandas) so every column gets exactly its type, even when all its values are empty
    import pyarrow
    import pyarrow.parquet
    arrow_types = {
        "string": pyarrow.string(),
        "int32": pyarrow.int32(),
        "int8": pyarrow.int8(),
        "float32": pyarrow.float32(),
        "bool": pyarrow.bool_(),
    }
    fields = []
    for name, (kind, required) in column_types.items():
        fields.append(pyarrow.field(name, arrow_types[kind], nullable=not required))
    table = pyarrow.Table.from_pylist(rows, schema=pyarrow.schema(fields))
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    pyarrow.parquet.write_table(table, tmp)
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(description="Build the common tables from the raw datasets.")
    parser.add_argument("--root", required=True, help="the datasets folder")
    parser.add_argument("--only", default="", help="comma separated: speechjudge,speecharena,mango,somos,bvcc")
    parser.add_argument("--force", action="store_true", help="rebuild tables that already exist")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    out = root / "_harmonized"
    out.mkdir(parents=True, exist_ok=True)
    wanted = [name for name in args.only.split(",") if name]
    if not wanted:
        wanted = DATASETS
    counts_path = out / "counts.json"
    counts = load_json(counts_path, default={})

    with open(out / "build.log", "a") as log_file:
        for name in wanted:
            already_built = True
            for kind in TABLE_KINDS[name]:
                if not (out / f"{name}_{kind}.parquet").exists():
                    already_built = False
            if already_built and not args.force:
                log(f"{name}: tables already built, skipped (use --force to rebuild)", log_file)
                continue

            log(f"{name}: loading", log_file)
            try:
                tables = load_dataset(name, root)
            except FileNotFoundError as error:
                log(f"{name}: SKIPPED, source not found: {error}", log_file)
                continue

            for kind, rows in tables.items():
                key = f"{name}_{kind}"
                column_types, validator = table_columns(kind)
                bad = count_invalid(rows, validator, key, log_file)
                message = f"{key}: {len(rows)} rows, {bad} invalid"
                expected = EXPECTED.get(key)
                if expected:
                    if expected == len(rows):
                        message += f", expected {expected} -> OK"
                    else:
                        message += f", expected {expected} -> DIFFERENT"
                log(message, log_file)
                if bad:
                    log(f"{key}: NOT written because of invalid rows", log_file)
                    continue
                write_parquet(rows, column_types, out / f"{key}.parquet")
                counts[key] = len(rows)
                save_json(counts_path, counts)
        log("done", log_file)


if __name__ == "__main__":
    main()
