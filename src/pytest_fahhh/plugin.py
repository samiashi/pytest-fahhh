"""Pytest plugin that plays a bundled meme sound on test failures."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import warnings
from importlib.resources import as_file, files
from pathlib import Path

import pytest

_DISABLED_ENV_VALUES = {"1", "true", "yes", "on"}
_MISSING_PLAYER_WARNING_EMITTED = False


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register plugin configuration."""
    group = parser.getgroup("fahhh")
    group.addoption(
        "--no-fahhh",
        action="store_true",
        default=False,
        help="Disable the pytest-fahhh failure sound for this run.",
    )
    parser.addini(
        "fahhh",
        "Play the bundled fahhh sound when a test fails.",
        type="bool",
        default=True,
    )


def _is_disabled(config: pytest.Config) -> bool:
    """Return whether the plugin is disabled for this pytest run."""
    if config.getoption("no_fahhh"):
        return True

    disabled_by_env = os.getenv("PYTEST_FAHHH_DISABLE", "").strip().lower()
    if disabled_by_env in _DISABLED_ENV_VALUES:
        return True

    return not config.getini("fahhh")


def _player_commands(sound_path: Path) -> list[list[str]]:
    """Return supported player commands for the current platform."""
    sound = str(sound_path)

    if sys.platform == "darwin":
        return [["afplay", sound]]

    if sys.platform.startswith("linux"):
        return [
            ["paplay", sound],
            ["aplay", sound],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", sound],
            ["mpg123", "-q", sound],
        ]

    return []


def _find_player_command(sound_path: Path) -> list[str] | None:
    """Return the first available audio player command."""
    for command in _player_commands(sound_path):
        if shutil.which(command[0]):
            return command
    return None


def _warn_missing_player() -> None:
    """Emit a single warning when no supported audio player is available."""
    global _MISSING_PLAYER_WARNING_EMITTED

    if _MISSING_PLAYER_WARNING_EMITTED:
        return

    _MISSING_PLAYER_WARNING_EMITTED = True
    warnings.warn(
        pytest.PytestWarning(
            "pytest-fahhh could not find a supported audio player. "
            "macOS uses afplay; Linux uses paplay, aplay, ffplay, or mpg123. "
            "Use --no-fahhh or PYTEST_FAHHH_DISABLE=1 to disable the plugin."
        ),
        stacklevel=2,
    )


def _launch_player(command: list[str]) -> None:
    """Start audio playback without blocking pytest output."""
    popen_kwargs: dict[str, object] = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name != "nt":
        popen_kwargs["start_new_session"] = True

    subprocess.Popen(command, **popen_kwargs)


def play_failure_sound() -> None:
    """Play the packaged fahhh sound if a supported player is installed."""
    resource = files("pytest_fahhh").joinpath("fahhh.mp3")
    with as_file(resource) as sound_path:
        command = _find_player_command(sound_path)
        if command is None:
            _warn_missing_player()
            return

        try:
            _launch_player(command)
        except OSError:
            _warn_missing_player()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[object]
) -> object:
    """Play the sound when the test call phase fails."""
    outcome = yield
    report = outcome.get_result()

    if _is_disabled(item.config):
        return

    if report.when != "call" or not report.failed or getattr(report, "wasxfail", False):
        return

    play_failure_sound()
