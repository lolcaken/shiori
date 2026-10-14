"""Tests for shiori.cli.entrypoint — the pipeline and its exit codes."""
import os

import shiori.cli.entrypoint as entrypoint
from shiori.core.errors import PreflightError
from shiori.core.models import RunSummary


def bomb_resolve(*args, **kwargs):
    raise AssertionError("channel resolution must be skipped on dry-run with --channel-name")


def test_dry_run_prints_commands_without_touching_the_network(monkeypatch, capsys):
    monkeypatch.setattr(entrypoint, "resolve_channel_name", bomb_resolve)
    code = entrypoint.main([
        "https://www.youtube.com/@SomeChannel",
        "--type", "all",
        "--dry-run",
        "--channel-name", "Some Channel",
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "yt-dlp" in out
    assert "/videos" in out and "/shorts" in out and "/streams" in out


def test_preflight_failure_returns_exit_code_3(monkeypatch, capsys):
    def failing_preflight(binary):
        raise PreflightError("no ffmpeg")

    monkeypatch.setattr(entrypoint, "preflight", failing_preflight)
    code = entrypoint.main(["https://www.youtube.com/@SomeChannel"])
    assert code == 3
    assert "no ffmpeg" in capsys.readouterr().err


def test_invalid_options_return_exit_code_2(capsys):
    code = entrypoint.main(["https://www.youtube.com/@SomeChannel", "-j", "0"])
    assert code == 2


def test_run_writes_a_log_file_next_to_the_archive(monkeypatch, tmp_path, capsys):
    seen = {}

    def fake_run_all(plans, runner=None, fail_fast=False, probe=None, parallel=None):
        seen["probe"] = probe
        return RunSummary()

    monkeypatch.setattr(entrypoint, "run_all", fake_run_all)
    code = entrypoint.main([
        "https://www.youtube.com/@SomeChannel",
        "-o", str(tmp_path),
        "--channel-name", "Some Channel",
    ])
    assert code == 0
    assert callable(seen["probe"])  # tab-existence probe is wired through
    logs = list((tmp_path / "Some Channel" / ".shiori-logs").glob("*.log"))
    assert len(logs) == 1
    assert "shiori: archiving Some Channel" in logs[0].read_text(encoding="utf-8")


def test_second_concurrent_run_is_refused(monkeypatch, tmp_path, capsys):
    channel = tmp_path / "Some Channel"
    channel.mkdir(parents=True)
    (channel / ".shiori-lock").write_text(f"{os.getpid()}\n", encoding="utf-8")
    code = entrypoint.main([
        "https://www.youtube.com/@SomeChannel",
        "-o", str(tmp_path),
        "--channel-name", "Some Channel",
    ])
    assert code == 1
    assert "another shiori run" in capsys.readouterr().err


def test_lock_is_released_after_the_run(monkeypatch, tmp_path):
    monkeypatch.setattr(
        entrypoint, "run_all", lambda plans, runner=None, fail_fast=False, probe=None, parallel=None: RunSummary()
    )
    entrypoint.main([
        "https://www.youtube.com/@SomeChannel",
        "-o", str(tmp_path),
        "--channel-name", "Some Channel",
    ])
    assert not (tmp_path / "Some Channel" / ".shiori-lock").exists()


def test_no_log_disables_the_log_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        entrypoint, "run_all", lambda plans, runner=None, fail_fast=False, probe=None, parallel=None: 
RunSummary()
    )
    code = entrypoint.main([
        "https://www.youtube.com/@SomeChannel",
        "-o", str(tmp_path),
        "--channel-name", "Some Channel",
        "--no-log",
    ])
    assert code == 0
    assert not (tmp_path / "Some Channel" / ".shiori-logs").exists()
