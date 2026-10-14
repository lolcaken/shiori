"""Pure planning: Options + resolved channel name -> one DownloadPlan per tab."""
from __future__ import annotations

from pathlib import Path

from akari.channel.tabs import spec_for
from akari.channel.urls import normalize_channel_url, tab_url
from akari.core.models import DownloadPlan, Options
from akari.naming.folder import sanitize_folder_name
from akari.naming.subtags import subtitle_tag
from akari.naming.templates import video_filename_template
from akari.planner import flag_sets


def build_plans(
    options: Options, channel_name: str, subtitle_dir: Path
) -> list[DownloadPlan]:
    base_url = normalize_channel_url(options.url)
    folder = sanitize_folder_name(channel_name)
    tag = subtitle_tag(options.sub_langs)
    filename = video_filename_template(tag)

    channel_dir = options.output_dir / folder
    archive_path = channel_dir / ".akari-archive.txt"

    plans = []
    for tab in options.tabs:
        spec = spec_for(tab)
        tab_dir = channel_dir / spec.folder
        argv = [
            options.yt_dlp,
            "--ignore-config",
            "--yes-playlist",
            *flag_sets.resume_flags(archive_path, options.full),
            *flag_sets.subtitle_flags(options.sub_langs),
            *flag_sets.subtitle_output_flags(subtitle_dir),
            *flag_sets.metadata_flags(),
            *flag_sets.format_flags(),
            "-o", str(tab_dir / filename),
            *flag_sets.network_flags(options.jobs, options.sleep_interval),
            *flag_sets.throttle_flags(
                options.throttled_rate, options.http_chunk_size, options.force_ipv4
            ),
            *flag_sets.filesystem_flags(),
            *flag_sets.date_flags(options.since, options.until),
            *(
                ["--cookies", str(options.cookies)]
                if options.cookies is not None
                else []
            ),
            tab_url(base_url, tab),
        ]
        plans.append(
            DownloadPlan(
                tab=tab,
                url=tab_url(base_url, tab),
                channel_name=channel_name,
                channel_folder=folder,
                tab_dir=tab_dir,
                archive_path=archive_path,
                argv=argv,
            )
        )
    return plans
