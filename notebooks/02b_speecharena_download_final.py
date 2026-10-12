# Download cell (A5) of notebook 02, final version: the one that downloaded datasets/speecharena_hi_AB.
# It runs inside notebook 02 and uses its variables (fs, plans, OUT, DS, SAB_SHA, SAB_REPO, LANG, SHARD_LIMIT,
# TIER_A, TIER_B, TIER_C, log). Rerunning it skips finished shards and retries only the failed ones.

RUN_DOWNLOAD = False     # <- set True to download the kept pairs
HASH_OUTPUT = True       # sha256 of each written file, saved in the manifest
BLOCK_MB = 32            # read each shard in big 32 MB blocks instead of many small requests
PLAN_CACHE = DS / "speecharena_hi_plan_cache.json"   # same path as in the planning cell, so this cell also works on its own


def save_plan_cache(plans):
    """Save the plans, so a restart can reload them instead of repeating the ~20 minute planning."""
    saved_plans = []
    for plan in plans:
        saved = dict(plan)
        saved["pairs"] = dict(plan["pairs"])
        saved["unknown_systems"] = sorted(plan["unknown_systems"])
        saved_plans.append(saved)
    PLAN_CACHE.write_text(json.dumps({"revision": SAB_SHA, "shard_limit": SHARD_LIMIT, "plans": saved_plans}))


def log_run(message):
    """log() a message and also append it to run.log next to the downloaded files."""
    log(message)
    with open(OUT / "run.log", "a") as run_log:
        run_log.write(message + "\n")


def sha256_of(path):
    """sha256 of a file, read in 4 MB pieces."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            piece = f.read(4 * 1024 * 1024)
            if not piece:
                break
            h.update(piece)
    return h.hexdigest()


def process_shard(plan):
    """Download the kept rows of one shard. Returns (status, number of pairs)."""
    name = plan["path"].split("/")[-1]
    final = OUT / name
    tmp = OUT / (name + ".tmp")
    expected = sum(plan["keep"])
    if expected == 0:
        return "no kept pairs", 0
    if final.exists() and pyarrow.parquet.ParquetFile(final).metadata.num_rows == expected:
        # finished in an earlier run (a shard gets its final name only when it is complete)
        return "already done", expected
    tmp.unlink(missing_ok=True)
    writer = None
    offset = 0
    written = 0
    with fs.open(plan["path"], "rb", block_size=BLOCK_MB * 1024 * 1024) as f:
        parquet_file = pyarrow.parquet.ParquetFile(f)
        for group, n in enumerate(plan["rg_rows"]):
            mask = plan["keep"][offset:offset + n]
            if any(mask):
                # only rows of allowed systems are kept
                table = parquet_file.read_row_group(group).filter(pyarrow.array(mask))
                row_numbers = []
                for j in range(n):
                    if mask[j]:
                        row_numbers.append(offset + j)
                table = table.append_column("src_shard", pyarrow.array([name] * len(row_numbers)))
                table = table.append_column("src_row", pyarrow.array(row_numbers, type=pyarrow.int64()))
                if writer is None:
                    writer = pyarrow.parquet.ParquetWriter(tmp, table.schema)
                writer.write_table(table)
                written += len(row_numbers)
            offset += n
    writer.close()
    tmp.replace(final)   # a half-written shard never carries the final name
    return "wrote", written


if not RUN_DOWNLOAD:
    log("RUN_DOWNLOAD is False: nothing downloaded or written.")
else:
    OUT.mkdir(parents=True, exist_ok=True)
    save_plan_cache(plans)
    log_run(f"start: {len(plans)} shards, {BLOCK_MB} MB blocks, {time.strftime('%Y-%m-%d %H:%M:%S')}")
    t_start = time.time()
    failed = []
    done = 0
    for plan in plans:
        name = plan["path"].split("/")[-1]
        try:
            status, count = process_shard(plan)
            done += 1
            log_run(f"[{done}/{len(plans)}] {name}: {status} ({count} pairs) | elapsed {time.time() - t_start:.0f}s")
        except Exception as error:
            # one failed shard does not stop the others
            failed.append(name)
            log_run(f"FAILED {name}: {type(error).__name__}: {str(error)[:200]}")

    if failed:
        log_run(f"{len(failed)} shard(s) failed: {sorted(failed)}. Run this cell again: finished shards are skipped, only these are retried.")
    else:
        files = {}
        kept_total = 0
        mixed_total = 0
        pair_counts = collections.Counter()
        for plan in plans:
            expected = sum(plan["keep"])
            kept_total += expected
            mixed_total += plan["mixed_kept"]
            pair_counts.update(plan["pairs"])
            if expected:
                name = plan["path"].split("/")[-1]
                rows = pyarrow.parquet.ParquetFile(OUT / name).metadata.num_rows
                files[name] = {"rows": rows, "bytes": (OUT / name).stat().st_size}
        if HASH_OUTPUT:
            for name in files:
                files[name]["sha256"] = sha256_of(OUT / name)
        manifest = {
            "source": f"https://huggingface.co/datasets/{SAB_REPO}", "revision": SAB_SHA, "lang": LANG,
            "rule": "keep a pair only if both systems are in tier A or B; tier C never written",
            "tier_a": sorted(TIER_A), "tier_b": sorted(TIER_B), "tier_c_excluded": sorted(TIER_C),
            "shards_processed": len(plans), "all_shards": SHARD_LIMIT is None,
            "pairs_kept": kept_total, "mixed_kept": mixed_total, "pairs_by_system_pair": dict(pair_counts),
            "files": files, "workers": 1, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        log_run(f"\nDone: {kept_total} pairs kept ({mixed_total} mixed) in {time.time() - t_start:.0f}s. Manifest: {OUT / 'manifest.json'}")
        if kept_total == 4444 and mixed_total == 1159:
            log_run("expected for all shards: 4444 pairs, 1159 mixed -> MATCH")
        else:
            log_run("expected for all shards: 4444 pairs, 1159 mixed -> DIFFERENT, investigate")
