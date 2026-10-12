# Download cell (A5) of notebook 02, earlier resumable version (replaced by 02b_speecharena_download_final.py).
# It runs inside notebook 02 and uses its variables (fs, plans, OUT, DS, SAB_SHA, SAB_REPO, LANG, SHARD_LIMIT,
# TIER_A, TIER_B, TIER_C). Rerunning it skips shards that are already complete.

RUN_DOWNLOAD = False     # <- set True to download the kept pairs
HASH_OUTPUT = True       # sha256 of each written file, saved in the manifest
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


def write_kept_rows(plan, name, target):
    """Read only the row groups with kept rows, keep only those rows, add src_shard and src_row, write to target."""
    writer = None
    offset = 0
    written = 0
    with fs.open(plan["path"], "rb") as f:
        parquet_file = pyarrow.parquet.ParquetFile(f)
        for group, n in enumerate(plan["rg_rows"]):
            mask = plan["keep"][offset:offset + n]
            if any(mask):
                table = parquet_file.read_row_group(group).filter(pyarrow.array(mask))
                row_numbers = []
                for j in range(n):
                    if mask[j]:
                        row_numbers.append(offset + j)
                table = table.append_column("src_shard", pyarrow.array([name] * len(row_numbers)))
                table = table.append_column("src_row", pyarrow.array(row_numbers, type=pyarrow.int64()))
                if writer is None:
                    writer = pyarrow.parquet.ParquetWriter(target, table.schema)
                writer.write_table(table)
                written += len(row_numbers)
            offset += n
    writer.close()
    return written


if not RUN_DOWNLOAD:
    print("RUN_DOWNLOAD is False: nothing downloaded or written.")
else:
    save_plan_cache(plans)
    OUT.mkdir(parents=True, exist_ok=True)
    pair_counts = collections.Counter()
    files = {}
    kept_total = 0
    mixed_total = 0
    t_start = time.time()
    for i, plan in enumerate(plans):
        name = plan["path"].split("/")[-1]
        final = OUT / name
        tmp = OUT / (name + ".tmp")
        expected = sum(plan["keep"])
        if expected == 0:
            print(f"[{i + 1}/{len(plans)}] {name}: no kept pairs, skipped")
            continue
        if final.exists() and pyarrow.parquet.ParquetFile(final).metadata.num_rows == expected:
            # finished in an earlier run (the file gets its final name only when it is complete)
            written = expected
            print(f"[{i + 1}/{len(plans)}] {name}: already done ({written} pairs), skipped")
        else:
            tmp.unlink(missing_ok=True)
            written = write_kept_rows(plan, name, tmp)
            tmp.replace(final)   # a half-written shard never carries the final name
            print(f"[{i + 1}/{len(plans)}] {name}: wrote {written} pairs, {final.stat().st_size / 1e6:.0f} MB, "
                  f"elapsed {time.time() - t_start:.0f}s")
        pair_counts.update(plan["pairs"])
        kept_total += written
        mixed_total += plan["mixed_kept"]
        files[name] = {"rows": written, "bytes": final.stat().st_size}
    if HASH_OUTPUT:
        for name in files:
            files[name]["sha256"] = sha256_of(OUT / name)
    manifest = {
        "source": f"https://huggingface.co/datasets/{SAB_REPO}", "revision": SAB_SHA, "lang": LANG,
        "rule": "keep a pair only if both systems are in tier A or B; tier C never written",
        "tier_a": sorted(TIER_A), "tier_b": sorted(TIER_B), "tier_c_excluded": sorted(TIER_C),
        "shards_processed": len(plans), "all_shards": SHARD_LIMIT is None,
        "pairs_kept": kept_total, "mixed_kept": mixed_total, "pairs_by_system_pair": dict(pair_counts),
        "files": files, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nDone: {kept_total} pairs kept ({mixed_total} mixed) in {time.time() - t_start:.0f}s. Manifest: {OUT / 'manifest.json'}")
    if kept_total == 4444 and mixed_total == 1159:
        print("expected for all shards: 4444 pairs, 1159 mixed -> MATCH")
    else:
        print("expected for all shards: 4444 pairs, 1159 mixed -> DIFFERENT, investigate")
