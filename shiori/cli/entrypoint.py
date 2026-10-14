"""Wire the pipeline: parse -> preflight -> resolve -> plan -> run -> report."""
from __future__ import annotations

import shlex
import sys

from shiori.channel.urls import normalize_channel_url
from shiori.cli.options import options_from_namespace
from shiori.cli.parser import build_parser
from shiori.core.errors import ShioriError
from shiori.planner.builder import build_plans
from shiori.runner.logfile import log_session
from shiori.runner.preflight import preflight
from shiori.runner.reporting import format_summary
from shiori.runner.resolve import resolve_channel_name
from shiori.runner.scratch import scratch_dir
from shiori.runner.sequencer import run_all


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
        if options.no_log:
            return _execute(options, tools, plans, channel_name)
        log_dir = (
            options.output_dir / plans[0].channel_folder / ".shiori-logs"
        )
        with log_session(log_dir):
            return _execute(options, tools, plans, channel_name)


def _execute(options, tools: dict[str, str], plans, channel_name: str) -> int:
    print(f"shiori: archiving {channel_name} "
          f"(yt-dlp {tools['yt-dlp']}, {tools['ffmpeg'].splitlines()[0]})")
    summary = run_all(plans, fail_fast=options.fail_fast)
    print(format_summary(summary))
    return 0 if summary.all_ok else 1
