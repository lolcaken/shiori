<p align="center">
  <img src="https://raw.githubusercontent.com/lolcaken/shiori/master/assets/logos/shiori-1-ytdlp-homage.svg" width="160" alt="Shiori logo: a red badge with a download arrow carrying a play button">
</p>

<h1 align="center">Shiori</h1>

<p align="center"><i>栞 — "bookmark." Your channel's bookmark.</i></p>

<p align="center">
  <a href="https://github.com/lolcaken/shiori/actions/workflows/test.yml"><img src="https://github.com/lolcaken/shiori/actions/workflows/test.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT license">
</p>

<p align="center">Point Shiori at a YouTube channel. Come back later and run it again.</p>

---

## What it does

Shiori archives a whole YouTube channel to plain `.mp4` files on your disk:

- **Videos, shorts, livestreams** — pick one tab or take all three, each landing in its own folder.
- **Captions baked in as soft subtitles** — both the uploader's subtitles *and* YouTube's auto-generated ones ride along inside the mp4 as toggleable text tracks. The video itself is never re-encoded, and no `.vtt` files are left behind.
- **Incremental by default** — every run records video IDs in `.shiori-archive.txt`, so re-running a 500-video channel fetches only the new uploads.
- **Untouched download output** — yt-dlp's own progress streams straight to your terminal, exactly as it emits it. Tab headers, a per-tab summary, and a timestamped log file wrap around it.

Shiori is a thin, opinionated wrapper around [yt-dlp](https://github.com/yt-dlp/yt-dlp). It has **zero runtime dependencies** — everything else is the Python standard library.

## Requirements

- Python 3.11+
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) on your `PATH`
- [`ffmpeg`](https://ffmpeg.org/) on your `PATH` (merging formats and embedding subtitles both go through it — Shiori checks for both before doing anything)

## Install

Requires Python 3.11+, [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [ffmpeg](https://ffmpeg.org/) on your `PATH`. Works on Windows, Linux, and macOS — the code is stdlib-only with no platform-specific dependencies, and CI runs the full suite on Windows + Ubuntu.

From PyPI (simplest):

```powershell
pip install shiori-archiver
```

From source:

```powershell
git clone https://github.com/lolcaken/shiori.git
cd shiori
pip install -e .
```

Linux quick setup (Debian/Ubuntu):

```bash
sudo apt-get install -y ffmpeg
pip install shiori-archiver yt-dlp
```

macOS:

```bash
brew install ffmpeg
pip install shiori-archiver yt-dlp
```

## Quick start

```powershell
# Archive a channel's videos
shiori "https://www.youtube.com/@SomeChannel"

# Everything: videos + shorts + livestreams
shiori "https://www.youtube.com/@SomeChannel" --type all
```

Bare handles work too: `shiori @SomeChannel`. It also accepts `/channel/…`, `/c/…` and `/user/…` URLs.

A real session looks like this (yt-dlp's own output streams straight through):

```
shiori: archiving YouTube (yt-dlp 2026.08.19, ffmpeg version N-125365-g9a01c1cb6a-20260630)
== shorts ==  https://www.youtube.com/@YouTube/shorts
[download] 100% of  448.87KiB in 00:00:00 at 926.63KiB/s
[Merger] Merging formats into ".../2026-10-13 - carrying the pots and pans is a rite of passage @andrewtrs [en].mp4"
  downloaded 9.5 MiB (1 file)
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

Run the same command weekly, monthly, whenever. Videos already in `.shiori-archive.txt` are skipped by yt-dlp, so only new uploads download:

```
== shorts ==  https://www.youtube.com/@SomeChannel/shorts
[download] Q_BC8ZhiZoU: carrying the pots and pans is a rite of passage @andrewtrs has already been recorded in the archive
  downloaded 0 B (0 files)
Archive run: 1 tab, 1 ok, 0 failed
```

`--full` ignores the archive file and rebuilds everything from scratch.

## Bot checks ("Please sign in" with no cookies)

Some videos answer every default request with `ERROR: … Please sign in` — that's YouTube's bot-check wall (IP-reputation based), not a broken video. Tested October 2026 against a gated short: the `default`, `android`, `ios`, `mweb`, `tv` and `web_safari` clients all hit the wall, while **`web_embedded` sailed through** with identical quality (720p h264 + AAC — the same `136+140` pick the defaults make):

```powershell
shiori "https://www.youtube.com/@SomeChannel" --type all `
  --extractor-args "youtube:player_client=web_embedded"
```

Notes, honestly stated:

- `--extractor-args` is a generic passthrough (repeatable) precisely because these gates move — today's recipe may need adjusting tomorrow, and that shouldn't require a shiori release.
- If *every* client fails on a video, your IP is hard-flagged: change networks, slow down, or accept cookies for those items. Static hardcoded PO tokens don't work anymore (YouTube binds them per video); the heavy alternative is the bgutil PO-token server plus its yt-dlp plugin.
- Cookies remain the reliable fix whenever they're an option.

## Missing tabs & partial runs

Not every channel has every tab. If `@SomeChannel` has no livestreams, that tab is skipped — not failed:

```
== streams ==  https://www.youtube.com/@SomeChannel/streams
  -- no streams tab, skipping
```

Similarly, a tab where some videos fail (gated items, deletions) but others download reports `completed with errors` and counts toward success — only a tab that errors with *nothing* new downloaded is a real `FAIL` (exit 1). A re-run of a healthy archive is all skips and `0 B` lines, exiting 0.

## Heavy use

Big channels mean long runs. Shiori parallelizes across videos, not fragments:

```powershell
shiori "https://www.youtube.com/@SomeChannel" --type all --workers 3
```

Each worker runs the exact same flags a single-shot run would use, on its own slice of video URLs with its own archive shard file — the fetched bytes are identical, only the concurrency differs, so **quality is untouched**. Shards merge back into `.shiori-archive.txt` when the tab finishes, and a live `143/500 videos` line tracks progress. `--workers 1` restores strict sequential mode; already-archived IDs are filtered before splitting, so a fully-archived tab skips downloading entirely.

Three guards keep long runs safe:

- **Disk check** — refuses to start below `--min-disk-gb` free space (default 5 GiB, `0` disables).
- **Channel lock** — one run per channel folder at a time (`.shiori-lock`, stale locks from dead runs are taken over). `--no-lock` opts out.
- **Cheap tab probes** — existence checks list a single item, so even 10k-video tabs start fast.

For full output capture (shiori streams yt-dlp's own log straight to your terminal), mirror it yourself:

```powershell
shiori "https://www.youtube.com/@SomeChannel" --type all *>&1 | Tee-Object run.log
```

## Options

```
usage: shiori [-h] [-o OUTPUT] [-t {videos,shorts,all}]
              [--sub-langs SUB_LANGS] [--since SINCE] [--until UNTIL]
              [--full] [-j JOBS] [--cookies COOKIES] [--dry-run]
              [--yt-dlp YT_DLP] [--fail-fast] [--channel-name CHANNEL_NAME]
              [--sleep SLEEP] [--throttled-rate THROTTLED_RATE]
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
| `--workers N` | Videos downloaded in parallel per tab (default: 3, `1` is sequential) |
| `--min-disk-gb GB` | Refuse to start below this free space (default: 5.0, `0` disables) |
| `--no-lock` | Allow concurrent runs on one channel (risks archive corruption) |
| `--cookies FILE` | Netscape cookie jar, for age- or bot-gated channels (checked up front) |
| `--dry-run` | Print the exact `yt-dlp` commands without running anything |
| `--yt-dlp PATH` | yt-dlp binary to use (default: from `PATH`) |
| `--fail-fast` | Stop remaining tabs after the first failure |
| `--channel-name NAME` | Skip the channel-name lookup (keeps `--dry-run` fully offline) |
| `--sleep N` | Seconds between requests (default: 2.0) |
| `--throttled-rate R` | Re-extract when a download crawls below this (default: `100K`, `0` disables) |
| `--http-chunk-size S` | Size of chunked range requests (default: `10M`) |
| `--ipv4` | Force all connections over IPv4 |
| `--extractor-args IE:ARGS` | Pass raw args to an extractor (repeatable; see Bot checks) |
| `--no-log` | Don't write the per-run log file |

Exit codes: `0` success — including tabs that finished with errors or were skipped · `1` a tab failed outright (nothing new downloaded) · `2` bad usage · `3` missing yt-dlp/ffmpeg.

## How it works

One `yt-dlp` invocation per channel tab, with a curated flag set (`-t mp4`, soft-sub embedding, metadata + thumbnail embedding, throttle recovery). Subtitle files are routed into a temporary scratch directory for embedding and the whole tree is deleted afterwards — that's the mp4-only guarantee. Nothing is ever passed through a shell: argv is always a list, so `&` and `;` in video titles can't break out.

```
parse → preflight (yt-dlp + ffmpeg) → resolve channel name
      → plan one command per tab → per tab: check it exists → run → measure → report
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

## License

MIT — see [LICENSE](LICENSE).
