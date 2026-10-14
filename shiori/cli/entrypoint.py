"""Wire the pipeline: parse -> preflight -> resolve -> plan -> run -> report."""
from __future__ import annotations

import shlex
import sys

from shiori.channel.urls import normalize_channel_url
from shiori.cli.options import options_from_namespace
from shiori.cli.parser import build_parser
from shiori.core.errors import ShioriError
from shiori.planner.builder import build_plans
from shiori.runner.lockfile import acquire_lock, release_lock
from shiori.runner.logfile import log_session
from shiori.runner.preflight import check_disk_space, preflight
from shiori.runner.reporting import format_summary
from shiori.runner.resolve import check_tab_exists, resolve_channel_name
from shiori.runner.scratch import scratch_dir
from shiori.runner.sequencer import run_all
from shiori.runner.workers import run_plan_parallel


def main(argv: list[str] | None = None) -> int:
    try:
        return _run(argv)
    except ShioriError as exc:
        print(f"shiori: error: {exc}", file=sys.stderr)
        return exc.exit_code


def _run(argv: list[str] | None) -> int:
    options = options_from_namespace(build_parser().parse_args(argv))
    tools = preflight(options.yt_dlp)
    channel_url = normalize_channel_url(options.url)
    channel_name = (
        options.channel_name
        or resolve_channel_name(options.yt_dlp, channel_url)
    )

    with scratch_dir() as subtitle_dir:
        plans = build_plans(options, channel_name, subtitle_dir)
        if options.dry_run:
            for plan in plans:
                print(shlex.join(plan.argv))
            return 0
        check_disk_space(options.output_dir, options.min_disk_gb)
        lock = None
        if not options.no_lock:
            lock = acquire_lock(plans[0].archive_path.parent)
        try:
            if options.no_log:
                return _execute(options, tools, plans, channel_name, subtitle_dir)
            log_dir = (
                options.output_dir / plans[0].channel_folder / ".shiori-logs"
            )
            with log_session(log_dir):
                return _execute(options, tools, plans, channel_name, subtitle_dir)
        finally:
            if lock is not None:
                release_lock(lock)


def _execute(options, tools: dict[str, str], plans, channel_name: str, subtitle_dir) -> int:
    print(f"shiori: archiving {channel_name} "
          f"(yt-dlp {tools['yt-dlp']}, {tools['ffmpeg'].splitlines()[0]})")

    def probe(plan) -> None:
        check_tab_exists(options.yt_dlp, plan.url)

    def parallel(plan):
        return run_plan_parallel(
            plan,
            yt_dlp=options.yt_dlp,
            workers=options.workers,
            scratch_dir=subtitle_dir,
            full=options.full,
        )

    summary = run_all(
        plans,
        fail_fast=options.fail_fast,
        probe=probe,
        parallel=parallel if options.workers > 1 else None,
    )
    print(format_summary(summary))
    return 0 if summary.all_ok else 1
