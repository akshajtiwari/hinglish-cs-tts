"""Run manifests: each run saves what is needed to repeat it.

A run gets its own folder, <root>/<name>-<date>-<time>/, with a manifest.json file.
start_run() writes the manifest at the start, finish_run() adds the results at the end.
"""
import hashlib
import json
import os
import platform
import random
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from switchmos.files import load_json, save_json


def run_command(args, folder=None):
    """Run a command and return its output text, or None if it fails."""
    try:
        result = subprocess.run(args, cwd=folder, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_info():
    """The current git commit and whether there are uncommitted changes."""
    folder = Path(__file__).parent
    status = run_command(["git", "status", "--porcelain"], folder)
    return {
        "commit": run_command(["git", "rev-parse", "HEAD"], folder),
        "dirty": bool(status),
    }


def hardware_info():
    """Machine name, Python version, CPU count, GPU names and the torch version if torch is installed."""
    info = {
        "host": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpus": os.cpu_count(),
        "gpus": [],
    }
    if shutil.which("nvidia-smi"):
        gpus = run_command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
        if gpus:
            info["gpus"] = gpus.splitlines()
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda"] = torch.version.cuda
    except ImportError:
        pass
    return info


def set_seed(seed):
    """Seed Python's random, and numpy and torch when they are installed."""
    random.seed(seed)
    try:
        import numpy
        numpy.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def start_run(name, config, seed, root="runs", datasets=None, ledger_ids=None):
    """Create the run folder with a manifest.json and return the folder path."""
    set_seed(seed)
    started = datetime.now()
    run_dir = Path(root) / f"{name}-{started.strftime('%Y%m%d-%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=False)
    # sort_keys: the same config always gives the same hash, whatever the key order
    config_text = json.dumps(config, sort_keys=True, default=str)
    manifest = {
        "name": name,
        "started": started.isoformat(timespec="seconds"),
        "config": config,
        "config_sha256": hashlib.sha256(config_text.encode()).hexdigest(),
        "seed": seed,
        "datasets": datasets or {},
        "git": git_info(),
        "hardware": hardware_info(),
        "ledger_ids": ledger_ids or [],
        "argv": sys.argv,
        "status": "running",
    }
    save_json(run_dir / "manifest.json", manifest)
    return run_dir


def finish_run(run_dir, metrics=None, outputs=None, status="ok", notes=""):
    """Add the end time, results and output files to the manifest. Returns the manifest."""
    manifest = load_json(Path(run_dir) / "manifest.json")
    started = datetime.fromisoformat(manifest["started"])
    ended = datetime.now()
    manifest["ended"] = ended.isoformat(timespec="seconds")
    manifest["wall_clock_s"] = round((ended - started).total_seconds(), 1)
    manifest["status"] = status
    manifest["metrics"] = metrics or {}
    manifest["outputs"] = outputs or []
    manifest["notes"] = notes
    save_json(Path(run_dir) / "manifest.json", manifest)
    return manifest
