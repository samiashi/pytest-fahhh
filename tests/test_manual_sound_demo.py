"""Manual-only demo test for verifying the failure sound."""

from __future__ import annotations

import pytest


@pytest.mark.manual_sound_demo
def test_manual_sound_demo() -> None:
    """Intentionally fail so the plugin plays the bundled sound."""
    raise AssertionError(
        "Manual sound demo: this failure is intentional so "
        "pytest-fahhh plays the sound."
    )
