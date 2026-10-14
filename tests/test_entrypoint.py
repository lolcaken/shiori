"""Tests for akari.cli.entrypoint — the pipeline and its exit codes."""
import akari.cli.entrypoint as entrypoint
from akari.core.errors import PreflightError


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
