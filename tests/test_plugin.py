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


def _run_makereport_hook(*, item: SimpleNamespace, report: SimpleNamespace) -> None:
    """Execute the hookwrapper with a fake report."""
    hook = plugin.pytest_runtest_makereport(item, call=None)
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
