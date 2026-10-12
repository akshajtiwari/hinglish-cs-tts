"""Small helpers for saving files safely.

Every save is atomic: the data is first written to "<name>.tmp" and then renamed.
If the job or the server stops halfway, the real file is never left half-written.
"""
import hashlib
import json
from pathlib import Path


def save_text(path, text):
    """Write text to a file atomically (creates the folder if needed)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def save_json(path, data):
    """Save a dict or list as pretty JSON, atomically."""
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    save_text(path, text)


def load_json(path, default=None):
    """Load a JSON file, or return `default` if the file does not exist."""
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_csv(df, path):
    """Save a pandas DataFrame as CSV (without the index), atomically."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)


def file_hash(path, algorithm="sha256"):
    """Return the hex hash of a file ("sha256" or "md5"), reading it in 4 MB pieces."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while True:
            piece = f.read(4 * 1024 * 1024)
            if not piece:
                break
            h.update(piece)
    return h.hexdigest()
