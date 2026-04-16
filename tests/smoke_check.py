"""Release smoke test for installed distributions."""

from __future__ import annotations

from importlib.resources import files

from pytest_fahhh import __version__, plugin


def main() -> None:
    """Verify the built distribution can be imported and bundled data exists."""
    sound_file = files("pytest_fahhh").joinpath("fahhh.mp3")

    if not sound_file.is_file():
        raise SystemExit("Bundled sound file was not included in the distribution.")

    if not hasattr(plugin, "pytest_runtest_makereport"):
        raise SystemExit("pytest plugin hook is missing from the installed package.")

    print(f"pytest-fahhh {__version__} smoke test passed")


if __name__ == "__main__":
    main()
