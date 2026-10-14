<p align="center">
  <img src="assets/logos/shiori-1-ytdlp-homage.svg" width="160" alt="Shiori logo: a red badge with a download arrow carrying a play button">
</p>

<h1 align="center">Shiori</h1>

<p align="center"><i>栞 — "bookmark." Your channel's bookmark.</i></p>

<p align="center">Point Shiori at a YouTube channel. Come back later and run it again.</p>

---

## What it does

Shiori archives a whole YouTube channel to plain `.mp4` files on your disk:

- **Videos, shorts, livestreams** — pick one tab or take all three, each landing in its own folder.
- **Captions baked in as soft subtitles** — both the uploader's subtitles *and* YouTube's auto-generated ones ride along inside the mp4 as toggleable text tracks. The video itself is never re-encoded, and no `.vtt` files are left behind.
- **Incremental by default** — every run records video IDs in `.shiori-archive.txt`, so re-running a 500-video channel fetches only the new uploads.
- **Quiet, honest logs** — one live progress line per video, one `ok` line per finished file, skips collapsed to a single count, and every run mirrored to a timestamped log file.

Shiori is a thin, opinionated wrapper around [yt-dlp](https://github.com/yt-dlp/yt-dlp). It has **zero runtime dependencies** — everything else is the Python standard library.

## Requirements

- Python 3.11+
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) on your `PATH`
- [`ffmpeg`](https://ffmpeg.org/) on your `PATH` (merging formats and embedding subtitles both go through it — Shiori checks for both before doing anything)

## Install

```powershell
git clone https://github.com/<you>/shiori.git
cd shiori
pip install -e .
```

That registers the `shiori` command. (`python -m shiori` works too.)

## Quick start

```powershell
# Archive a channel's videos
shiori "https://www.youtube.com/@SomeChannel"

# Everything: videos + shorts + livestreams
shiori "https://www.youtube.com/@SomeChannel" --type all
```

Bare handles work too: `shiori @SomeChannel`. It also accepts `/channel/…`, `/c/…` and `/user/…` URLs.

A real session looks like this:

```
shiori: archiving YouTube (yt-dlp 2026.08.19, ffmpeg version N-125365-g9a01c1cb6a-20260630)
== shorts ==  https://www.youtube.com/@YouTube/shorts
  ok 2026-10-13 - carrying the pots and pans is a rite of passage @andrewtrs [en].mp4 (4.2s)
Archive run: 1 tab, 1 ok, 0 failed
```

## What you get

```
archives/
  Some Channel/
    .shiori-archive.txt          # incremental state — don't delete this
    .shiori-logs/
      20261014-202724.log        # one per run
    videos/
      2026-10-08 - 20 years of esports history explained [en].mp4
    shorts/
      2026-10-13 - carrying the pots and pans is a rite of passage @andrewtrs [en].mp4
    streams/
      ...
```

Filenames are `upload-date - title [subtitle-langs].mp4`. Every mp4 carries `h264` video, `aac` audio, `mov_text` subtitle tracks, and embedded cover art + metadata.

## Re-runs

Run the same command weekly, monthly, whenever. Already-archived videos collapse to one line per tab:

```
== shorts ==  https://www.youtube.com/@SomeChannel/shorts
  1 already archived
Archive run: 1 tab, 1 ok, 0 failed
```

`--full` ignores the archive file and rebuilds everything from scratch.

## Options

```
usage: shiori [-h] [-o OUTPUT] [-t {videos,shorts,all}]
              [--sub-langs SUB_LANGS] [--since SINCE] [--until UNTIL]
              [--full] [-j JOBS] [--cookies COOKIES] [--dry-run]
              [--yt-dlp YT_DLP] [--fail-fast] [--channel-name CHANNEL_NAME]
              [--sleep SLEEP] [--verbose] [--throttled-rate THROTTLED_RATE]
              [--http-chunk-size HTTP_CHUNK_SIZE] [--ipv4] [--no-log]
              url
```

| Flag | What it does |
|---|---|
| `-o, --output DIR` | Archive root (default: `./archives`) |
| `-t, --type` | `videos` (default), `shorts`, or `all` (videos + shorts + streams) |
| `--sub-langs LANGS` | Subtitle languages, yt-dlp syntax (default: `"en.*"`, use `"all"` for everything) |
| `--since / --until` | Date range filter (`YYYYMMDD`) |
| `--full` | Ignore the archive file, re-download everything |
| `-j, --jobs N` | Concurrent download fragments per video (default: 8) |
| `--cookies FILE` | Netscape cookie jar, for age- or bot-gated channels (checked up front) |
| `--dry-run` | Print the exact `yt-dlp` commands without running anything |
| `--yt-dlp PATH` | yt-dlp binary to use (default: from `PATH`) |
| `--fail-fast` | Stop remaining tabs after the first failure |
| `--channel-name NAME` | Skip the channel-name lookup (keeps `--dry-run` fully offline) |
| `--sleep N` | Seconds between requests (default: 2.0) |
| `--verbose` | Show raw yt-dlp output instead of the organized log |
| `--throttled-rate R` | Re-extract when a download crawls below this (default: `100K`, `0` disables) |
| `--http-chunk-size S` | Size of chunked range requests (default: `10M`) |
| `--ipv4` | Force all connections over IPv4 |
| `--no-log` | Don't write the per-run log file |

Exit codes: `0` success · `1` a tab failed (the rest still ran) · `2` bad usage · `3` missing yt-dlp/ffmpeg.

## How it works

One `yt-dlp` invocation per channel tab, with a curated flag set (`-t mp4`, soft-sub embedding, metadata + thumbnail embedding, throttle recovery). Subtitle files are routed into a temporary scratch directory for embedding and the whole tree is deleted afterwards — that's the mp4-only guarantee. Nothing is ever passed through a shell: argv is always a list, so `&` and `;` in video titles can't break out.

```
parse → preflight (yt-dlp + ffmpeg) → resolve channel name
      → plan one command per tab → run sequentially → report
```

## For hackers

```
shiori/
  cli/        argument surface + pipeline wiring
  core/       shared models and errors (each error carries an exit code)
  channel/    URL normalization, tab registry
  naming/     folder sanitizing, filename template, [lang] tag
  planner/    pure Options → argv (no I/O, fully tested)
  runner/     the only layer that touches the outside world
tests/        mirrors the package one-for-one, pytest, no network
```

```powershell
python -m pytest tests/ -q
```

## Why "Shiori"?

栞 (*shiori*) means **bookmark** — a guide slipped between pages so you can find your way back. That's the whole job: a bookmark for a channel, keeping your place while it grows.
