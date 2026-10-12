#!/usr/bin/env python3
"""Start (or resume) the SpeechJudge-Data and SOMOS downloads and print their progress.

Run on the server with the project venv (it needs huggingface_hub):
    PYTHONPATH=~/projects/switchmos_code/src ~/projects/hinglish-cs-tts/hinglishtts/bin/python \
        ~/projects/switchmos_code/scripts/step1_download/download_speechjudge_and_somos.py

Options:
    (none)   start or resume both downloads, then print a status line every 30 seconds
    --once   print one status line per download and exit (starts nothing)
    --stop   stop both downloads (partial files are kept; run again to resume)

How it works:
  * Each download runs as its own background process, so Ctrl-C, closing the laptop or an
    ssh drop does not stop it. Run the script again any time to watch it again.
  * Downloads resume from the bytes already on disk (wget -c for SOMOS; hf download skips finished files).
  * Marker files in logs/: .dl_<name>.pid (process id), .dl_<name>.rc (exit code when finished),
    .dl_<name>.ok (verified). A download with an .ok file is never started again.
  * When a download ends it is verified: SOMOS by size and md5 (the md5 Zenodo publishes),
    SpeechJudge by comparing every file's size with the file list on Hugging Face.
  * Events (start, finish, verification, a status line each minute) go to logs/dl_all.log.
"""
import argparse
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

from switchmos.files import file_hash

ROOT = Path.home() / "projects" / "hinglish-cs-tts"
LOGS = ROOT / "logs"
EVENT_LOG = LOGS / "dl_all.log"

SJ_REPO = "RMSnow/SpeechJudge-Data"
SJ_DIR = ROOT / "datasets" / "speechjudge"
SJ_SOURCE = "https://huggingface.co/datasets/RMSnow/SpeechJudge-Data"
SJ_WHY = "99K modern TTS preference pairs incl. zh-en code-switched slice = main modern training data and SpeechJudge-Eval test"

SOMOS_FILE = ROOT / "datasets" / "somos" / "somos.zip"
SOMOS_BYTES = 3_971_669_902
SOMOS_MD5 = "bdfde4cae256549dfab05d713136e4af"
SOMOS_URL = "https://zenodo.org/records/7378801/files/somos.zip?download=1"
SOMOS_SOURCE = "https://zenodo.org/records/7378801"
SOMOS_WHY = "375k absolute MOS ratings for scale and calibration"

CHECK_EVERY_S = 2
PRINT_EVERY_S = 30
LOG_EVERY_S = 60


def event(message):
    """Append one time-stamped line to the event log."""
    LOGS.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with open(EVENT_LOG, "a") as f:
        f.write(f"{now} {message}\n")


def folder_bytes(folder):
    """Total size in bytes of all files under a folder."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for name in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, name))
            except OSError:
                pass
    return total


def speechjudge_expected_sizes():
    """{file name: size in bytes} from the Hugging Face file list."""
    from huggingface_hub import HfApi
    info = HfApi().dataset_info(SJ_REPO, files_metadata=True)
    sizes = {}
    for file in info.siblings:
        if file.size is not None:
            sizes[file.rfilename] = file.size
    return sizes


def make_jobs():
    """One dict per download, with its command, size and marker files."""
    expected = speechjudge_expected_sizes()
    speechjudge = {
        "key": "speechjudge",
        "label": "SpeechJudge",
        "cmd": f'"{ROOT}/hinglishtts/bin/hf" download {SJ_REPO} --repo-type dataset --local-dir datasets/speechjudge',
        "total": sum(expected.values()),
        "expected": expected,
        "source": SJ_SOURCE,
        "why": SJ_WHY,
    }
    somos = {
        "key": "somos",
        "label": "SOMOS",
        "cmd": f'mkdir -p datasets/somos && wget -c -q --show-progress --progress=dot:mega -O datasets/somos/somos.zip "{SOMOS_URL}"',
        "total": SOMOS_BYTES,
        "source": SOMOS_SOURCE,
        "why": SOMOS_WHY,
    }
    jobs = [speechjudge, somos]
    for job in jobs:
        job["pid_file"] = LOGS / f".dl_{job['key']}.pid"
        job["rc_file"] = LOGS / f".dl_{job['key']}.rc"
        job["ok_file"] = LOGS / f".dl_{job['key']}.ok"
        job["out_log"] = LOGS / f"dl_{job['key']}.out"
        job["process"] = None
        job["bytes"] = 0
        job["state"] = "waiting"
        job["final"] = False
    return jobs


def bytes_on_disk(job):
    """How many bytes of this download are on disk now."""
    if job["key"] == "speechjudge":
        if SJ_DIR.exists():
            return folder_bytes(SJ_DIR)
        return 0
    if SOMOS_FILE.exists():
        return SOMOS_FILE.stat().st_size
    return 0


def verify(job):
    """Check a finished download. Returns (ok, detail text)."""
    if job["key"] == "speechjudge":
        expected = job["expected"]
        missing = 0
        wrong = 0
        for name, size in expected.items():
            path = SJ_DIR / name
            if not path.exists():
                missing += 1
            elif path.stat().st_size != size:
                wrong += 1
        if missing or wrong:
            return False, f"{missing} missing, {wrong} wrong size of {len(expected)} files"
        return True, f"all {len(expected)} files present with the size listed on Hugging Face ({job['total']} bytes)"
    size = bytes_on_disk(job)
    if size != SOMOS_BYTES:
        return False, f"size {size} != expected {SOMOS_BYTES}"
    got = file_hash(SOMOS_FILE, "md5")
    return got == SOMOS_MD5, f"md5 {got} (expected {SOMOS_MD5}), {SOMOS_BYTES} bytes"


def is_running(job):
    """True while the download process is still running."""
    if job["process"] is not None:
        return job["process"].poll() is None
    try:
        pid = int(job["pid_file"].read_text())
        # signal 0 sends nothing; it only checks that the process exists
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def start(job):
    """Start the download, or attach to one that is already running or finished."""
    if job["ok_file"].exists():
        job["state"] = "already complete and verified earlier"
        job["final"] = True
        job["bytes"] = bytes_on_disk(job)
        return
    if is_running(job):
        job["state"] = "running (attached to a download that was already started)"
        return
    job["rc_file"].unlink(missing_ok=True)
    if job["key"] == "somos" and bytes_on_disk(job) == SOMOS_BYTES:
        job["rc_file"].write_text("0")
        job["state"] = "all bytes already on disk, verifying next"
        event(f"{job['key']}: all bytes already present, skipping download")
        return
    event(f"SOURCE {job['source']} | WHY {job['why']}")
    event(f"START {job['key']} (resuming from {bytes_on_disk(job)} bytes on disk)")
    env = dict(os.environ)
    env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    # the shell writes the exit code to the .rc file when the download ends
    command = f'{job["cmd"]}; echo $? > "{job["rc_file"]}"'
    # start_new_session: the download keeps running when this script or the ssh session ends
    job["process"] = subprocess.Popen(
        ["bash", "-c", command],
        cwd=ROOT,
        stdout=open(job["out_log"], "ab"),
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    job["pid_file"].write_text(str(job["process"].pid))
    job["state"] = "running"


def stop(job):
    """Stop a running download. Returns True if a stop signal was sent."""
    try:
        pid = int(job["pid_file"].read_text())
        # the process started its own session, so its id is also the group id: this stops bash and the download
        os.killpg(pid, signal.SIGTERM)
    except (OSError, ValueError):
        return False
    event(f"STOP {job['key']} requested by user")
    return True


def update(job):
    """Refresh the byte count and the state; verify the download once it has finished."""
    job["bytes"] = bytes_on_disk(job)
    if job["final"]:
        return
    if is_running(job):
        job["state"] = "running"
        return
    rc = None
    if job["rc_file"].exists():
        rc = job["rc_file"].read_text().strip()
    if rc is None:
        job["state"] = "NOT RUNNING and not finished (stopped?). Run the script again to resume"
        job["final"] = True
        event(f"{job['key']}: stopped before finishing at {job['bytes']} bytes")
    elif rc != "0":
        job["state"] = f"FAILED (exit code {rc}). Run the script again to resume; see logs/dl_{job['key']}.out"
        job["final"] = True
        event(f"{job['key']}: FAILED rc={rc} at {job['bytes']} bytes")
    else:
        print(f"{job['label']}: download finished, verifying (this can take a minute)...", flush=True)
        ok, detail = verify(job)
        job["final"] = True
        if ok:
            job["state"] = "VERIFIED OK. " + detail
            job["ok_file"].write_text(detail)
            event(f"{job['key']}: VERIFIED OK {detail}")
        else:
            job["state"] = "VERIFICATION FAILED. " + detail
            event(f"{job['key']}: VERIFICATION FAILED {detail}")


def status_line(job, speed):
    """One readable line: name, percent, GB done, speed, state."""
    percent = 0.0
    if job["total"]:
        percent = min(100.0, 100.0 * job["bytes"] / job["total"])
    done_gb = job["bytes"] / 1e9
    total_gb = job["total"] / 1e9
    return f"{job['label']:<12} {percent:5.1f}%  {done_gb:7.2f} / {total_gb:7.2f} GB  {speed / 1e6:6.1f} MB/s  {job['state']}"


def all_final(jobs):
    """True when every download has finished, failed or stopped."""
    for job in jobs:
        if not job["final"]:
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Start or resume the SpeechJudge and SOMOS downloads.")
    parser.add_argument("--once", action="store_true", help="print one status line per download and exit; starts nothing")
    parser.add_argument("--stop", action="store_true", help="stop both downloads (partial files are kept)")
    args = parser.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    jobs = make_jobs()

    if args.stop:
        for job in jobs:
            if stop(job):
                print(f"{job['label']}: stop signal sent")
            else:
                print(f"{job['label']}: nothing running")
        return

    if args.once:
        for job in jobs:
            job["bytes"] = bytes_on_disk(job)
            if is_running(job):
                job["state"] = "running"
            print(status_line(job, 0))
        return

    for job in jobs:
        start(job)
    last_bytes = {}
    for job in jobs:
        last_bytes[job["key"]] = bytes_on_disk(job)
    last_print = time.time()
    last_log = 0.0
    try:
        while True:
            for job in jobs:
                update(job)
            now = time.time()
            if now - last_print >= PRINT_EVERY_S or all_final(jobs):
                lines = []
                for job in jobs:
                    speed = (job["bytes"] - last_bytes[job["key"]]) / max(now - last_print, 1)
                    last_bytes[job["key"]] = job["bytes"]
                    lines.append(status_line(job, max(speed, 0)))
                print(datetime.now().strftime("%H:%M:%S"), flush=True)
                for line in lines:
                    print("  " + line, flush=True)
                last_print = now
            if now - last_log >= LOG_EVERY_S:
                parts = []
                for job in jobs:
                    parts.append(f"{job['key']} {job['bytes']}/{job['total']} B {job['state']}")
                event("STATUS " + " | ".join(parts))
                last_log = now
            if all_final(jobs):
                break
            time.sleep(CHECK_EVERY_S)
    except KeyboardInterrupt:
        print("\nStopped watching. Downloads keep running in the background; run the script again to watch.")
        return
    print("\nAll downloads finished. Evidence: logs/dl_all.log")


if __name__ == "__main__":
    main()
