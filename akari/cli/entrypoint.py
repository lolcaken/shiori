"""Wire the pipeline: parse -> preflight -> resolve -> plan -> run -> report."""
from __future__ import annotations

import shlex
import sys

from akari.channel.urls import normalize_channel_url
from akari.cli.options import options_from_namespace
from akari.cli.parser import build_parser
from akari.core.errors import AkariError
from akari.planner.builder import build_plans
from akari.runner.preflight import preflight
from akari.runner.reporting import format_summary
from akari.runner.resolve import resolve_channel_name
from akari.runner.scratch import scratch_dir
from akari.runner.sequencer import run_all


def main(argv: list[str] | None = None) -> int:
    try:
        return _run(argv)
    except AkariError as exc:
        print(f"akari: error: {exc}", file=sys.stderr)
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
        print(f"akari: archiving {channel_name} "
              f"(yt-dlp {tools['yt-dlp']}, {tools['ffmpeg'].splitlines()[0]})")
        summary = run_all(plans, fail_fast=options.fail_fast)
        print(format_summary(summary))
        return 0 if summary.all_ok else 1
