"""Tests for shiori.runner.logfile — mirroring console output to a log file."""
import io

from shiori.runner.logfile import TeeWriter, log_session


def test_tee_collapses_carriage_return_status_to_its_final_line(tmp_path):
    log_path = tmp_path / "run.log"
    console = io.StringIO()
    tee = TeeWriter(console, log_path.open("w", encoding="utf-8"))
    tee.write("\r  dl 10% of 10MiB")
    tee.write("\r  dl 54% of 10MiB")
    tee.write("\r" + " " * 20 + "\r  ok video.mp4 (10MiB, 1.0s)\n")
    tee.write("Archive run: 1 tabs, 1 ok, 0 failed\n")
    tee.close()
    assert console.getvalue().count("dl ") == 2  # console still sees it all live
    content = log_path.read_text(encoding="utf-8")
    assert "dl " not in content  # ...but the file keeps only final states
    assert "ok video.mp4" in content
    assert "Archive run" in content


def test_log_session_writes_a_timestamped_log(tmp_path, capsys):
    with log_session(tmp_path):
        print("hello")
    out = capsys.readouterr().out
    assert "hello" in out
    logs = list(tmp_path.glob("*.log"))
    assert len(logs) == 1
    assert "hello" in logs[0].read_text(encoding="utf-8")


def test_log_session_falls_back_to_console_when_unwritable(tmp_path, capsys):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with log_session(blocker):  # mkdir on a file path raises OSError
        print("hello")
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "warning" in captured.err.lower()
