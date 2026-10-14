"""Run one tab's videos across parallel yt-dlp workers.

Each worker gets an equal-ish slice of video URLs plus its own archive
shard file; shards merge back into the main archive afterwards. Every
worker runs the exact same flag set the single-shot path builds, so the
fetched bytes are identical — only the concurrency differs.
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from shiori.core.models import DownloadPlan, TabOutcome
from shiori.planner.builder import worker_argv
from shiori.runner.archive import merge_archives, read_archive_ids
from shiori.runner.enumerate import list_tab_ids
from shiori.runner.process import run_argv


def chunk_ids(ids: list[str], workers: int) -> list[list[str]]:
    """Split ids into at most `workers` contiguous chunks."""
    if not ids or workers < 1:
        return []
    size = (len(ids) + workers - 1) // workers
    return [ids[i:i + size] for i in range(0, len(ids), size)]


def count_lines(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def monitor_progress(
    stop_event: threading.Event,
    shard_files: list[Path],
    total: int,
    label: str,
    interval: float = 10.0,
) -> None:
    """Poll shard archives and print `label: done/total videos` on change."""
    last = -1
    while not stop_event.wait(interval):
        done = sum(count_lines(path) for path in shard_files)
        if done != last:
            last = done
            print(f"  {label}: {done}/{total} videos", flush=True)


def run_shard_commands(
    argv_list: list[list[str]],
    max_workers: int,
    run_fn: Callable[[list[str]], int] = run_argv,
) -> list[int]:
    """Run worker commands concurrently, collecting return codes in order."""
    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as pool:
        return list(pool.map(run_fn, argv_list))


def write_batch_file(directory: Path, index: int, ids: list[str]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f".shiori-batch-{index}.txt"
    path.write_text(
        "".join(f"https://www.youtube.com/watch?v={video_id}\n" for video_id in ids),
        encoding="utf-8",
    )
    return path


def run_plan_parallel(
    plan: DownloadPlan,
    yt_dlp: str,
    workers: int,
    scratch_dir: Path,
    full: bool = False,
    list_ids: Callable = list_tab_ids,
    run_fn: Callable[[list[str]], int] = run_argv,
    monitor: bool = True,
) -> TabOutcome:
    """Download one tab with parallel workers, merging shards afterwards."""
    start = time.monotonic()
    try:
        ids = list_ids(yt_dlp, plan.url)
    except Exception:
        # Enumeration failed: fall back to the classic single-shot command
        # rather than failing a tab that might download just fine.
        returncode = run_fn(plan.argv)
        return TabOutcome(
            plan=plan, returncode=returncode, elapsed=time.monotonic() - start
        )
    archived = set() if full else read_archive_ids(plan.archive_path)
    todo = [video_id for video_id in ids if video_id not in archived]
    print(
        f"  {len(ids) - len(todo)} already archived, {len(todo)} to fetch",
        flush=True,
    )
    if not todo:
        return TabOutcome(
            plan=plan, returncode=0, elapsed=time.monotonic() - start
        )
    chunks = chunk_ids(todo, max(1, workers))
    shard_files: list[Path] = []
    argv_list: list[list[str]] = []
    for index, chunk in enumerate(chunks):
        batch = write_batch_file(scratch_dir, index, chunk)
        shard = scratch_dir / f".shiori-archive-shard-{index}.txt"
        shard_files.append(shard)
        argv_list.append(worker_argv(plan.argv, batch, shard))

    stop_event = threading.Event()
    monitor_thread = None
    if monitor:
        monitor_thread = threading.Thread(
            target=monitor_progress,
            kwargs=dict(
                stop_event=stop_event,
                shard_files=shard_files,
                total=len(todo),
                label=plan.tab.value,
            ),
            daemon=True,
        )
        monitor_thread.start()
    try:
        codes = run_shard_commands(argv_list, max_workers=len(chunks), run_fn=run_fn)
    finally:
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join(timeout=30)
    if not full:
        merge_archives(shard_files, plan.archive_path, plan.archive_path)
    returncode = next((code for code in codes if code != 0), 0)
    return TabOutcome(
        plan=plan, returncode=returncode, elapsed=time.monotonic() - start
    )
