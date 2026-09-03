"""Tests for the pytest-fahhh plugin."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pytest_fahhh import plugin


class DummyConfig:
    """Minimal pytest config stub for hook tests."""

    def __init__(self, *, no_fahhh: bool = False, ini_enabled: bool = True) -> None:
        self.no_fahhh = no_fahhh
        self.ini_enabled = ini_enabled

    def getoption(self, name: str) -> bool:
        assert name == "no_fahhh"
        return self.no_fahhh

    def getini(self, name: str) -> bool:
        assert name == "fahhh"
        return self.ini_enabled


class DummyOutcome:
    """Minimal pluggy outcome stub for hookwrapper tests."""

    def __init__(self, report: SimpleNamespace) -> None:
        self.report = report

    def get_result(self) -> SimpleNamespace:
        return self.report


class DummyCall:
    """Minimal pytest CallInfo stub for hook tests."""

    def __init__(self) -> None:
        self.when = "call"
        self.excinfo = None


def _run_makereport_hook(*, item: SimpleNamespace, report: SimpleNamespace) -> None:
    """Execute the hookwrapper with a fake report."""
    hook = plugin.pytest_runtest_makereport(item, call=DummyCall())
    next(hook)
    with pytest.raises(StopIteration):
        hook.send(DummyOutcome(report))


def test_find_player_command_prefers_afplay_on_macos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """macOS should use afplay when it is available."""
    monkeypatch.setattr(plugin.sys, "platform", "darwin")
    monkeypatch.setattr(plugin.shutil, "which", lambda command: "/usr/bin/afplay")

    command = plugin._find_player_command(Path("/tmp/fahhh.mp3"))

    assert command == ["afplay", "/tmp/fahhh.mp3"]


def test_find_player_command_linux_prefers_paplay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linux should prefer paplay when it is available."""
    monkeypatch.setattr(plugin.sys, "platform", "linux")
    monkeypatch.setattr(plugin.shutil, "which", lambda command: "/usr/bin/paplay")

    command = plugin._find_player_command(Path("/tmp/fahhh.mp3"))

    assert command == ["paplay", "/tmp/fahhh.mp3"]


def test_find_player_command_linux_falls_back_to_aplay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linux should fall back to aplay when paplay is unavailable."""
    monkeypatch.setattr(plugin.sys, "platform", "linux")

    def fake_which(command: str) -> str | None:
        return "/usr/bin/aplay" if command == "aplay" else None

    monkeypatch.setattr(plugin.shutil, "which", fake_which)

    command = plugin._find_player_command(Path("/tmp/fahhh.mp3"))

    assert command == ["aplay", "/tmp/fahhh.mp3"]


def test_find_player_command_linux_falls_back_to_ffplay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linux should fall back to ffplay when paplay and aplay are unavailable."""
    monkeypatch.setattr(plugin.sys, "platform", "linux")

    def fake_which(command: str) -> str | None:
        return "/usr/bin/ffplay" if command == "ffplay" else None

    monkeypatch.setattr(plugin.shutil, "which", fake_which)

    command = plugin._find_player_command(Path("/tmp/fahhh.mp3"))

    assert command == [
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "quiet",
        "/tmp/fahhh.mp3",
    ]


def test_find_player_command_linux_falls_back_to_mpg123(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linux should fall back to mpg123 when other players are unavailable."""
    monkeypatch.setattr(plugin.sys, "platform", "linux")

    def fake_which(command: str) -> str | None:
        return "/usr/bin/mpg123" if command == "mpg123" else None

    monkeypatch.setattr(plugin.shutil, "which", fake_which)

    command = plugin._find_player_command(Path("/tmp/fahhh.mp3"))

    assert command == ["mpg123", "-q", "/tmp/fahhh.mp3"]


def test_find_player_command_returns_none_on_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows should use PowerShell when it is available."""
    monkeypatch.setattr(plugin.sys, "platform", "win32")
    monkeypatch.setattr(plugin.shutil, "which", lambda command: "/usr/bin/powershell")

    command = plugin._find_player_command(Path("/tmp/fahhh.mp3"))

    assert command == [
        "powershell",
        "-c",
        "(New-Object Media.SoundPlayer '/tmp/fahhh.mp3').PlaySync();",
    ]


def test_find_player_command_returns_none_when_no_player_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Should return None when no player is available on the system."""
    monkeypatch.setattr(plugin.sys, "platform", "darwin")
    monkeypatch.setattr(plugin.shutil, "which", lambda command: None)

    command = plugin._find_player_command(Path("/tmp/fahhh.mp3"))

    assert command is None


def test_makereport_plays_sound_for_failed_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed test call should trigger audio playback."""
    monkeypatch.delenv("PYTEST_FAHHH_DISABLE", raising=False)
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig())
    report = SimpleNamespace(when="call", failed=True)

    _run_makereport_hook(item=item, report=report)

    assert calls == ["played"]


def test_makereport_respects_disable_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """The plugin should not play sound when explicitly disabled."""
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig(no_fahhh=True))
    report = SimpleNamespace(when="call", failed=True)

    _run_makereport_hook(item=item, report=report)

    assert calls == []


def test_makereport_respects_env_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The plugin should not play sound when PYTEST_FAHHH_DISABLE is set."""
    monkeypatch.setenv("PYTEST_FAHHH_DISABLE", "1")
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig())
    report = SimpleNamespace(when="call", failed=True)

    _run_makereport_hook(item=item, report=report)

    assert calls == []


def test_makereport_respects_ini_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The plugin should not play sound when fahhh ini option is false."""
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig(ini_enabled=False))
    report = SimpleNamespace(when="call", failed=True)

    _run_makereport_hook(item=item, report=report)

    assert calls == []


def test_makereport_skips_setup_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup phase failures should not trigger sound playback."""
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig())
    report = SimpleNamespace(when="setup", failed=True)

    _run_makereport_hook(item=item, report=report)

    assert calls == []


def test_makereport_skips_teardown_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Teardown phase failures should not trigger sound playback."""
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig())
    report = SimpleNamespace(when="teardown", failed=True)

    _run_makereport_hook(item=item, report=report)

    assert calls == []


def test_makereport_skips_passing_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Passing tests should not trigger sound playback."""
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig())
    report = SimpleNamespace(when="call", failed=False)

    _run_makereport_hook(item=item, report=report)

    assert calls == []


def test_makereport_skips_xfail_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests that fail as expected (xfail) should not trigger sound playback."""
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig())
    report = SimpleNamespace(when="call", failed=True, wasxfail="reason")

    _run_makereport_hook(item=item, report=report)

    assert calls == []


def test_makereport_skips_xpass(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests that unexpectedly pass (xpass) should not trigger sound playback."""
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig())
    report = SimpleNamespace(when="call", failed=True, wasxfail=True)

    _run_makereport_hook(item=item, report=report)

    assert calls == []


def test_makereport_skips_skipped_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skipped tests should not trigger sound playback."""
    calls: list[str] = []
    monkeypatch.setattr(plugin, "play_failure_sound", lambda: calls.append("played"))

    item = SimpleNamespace(config=DummyConfig())
    report = SimpleNamespace(when="call", failed=False, skipped=True)

    _run_makereport_hook(item=item, report=report)

    assert calls == []
