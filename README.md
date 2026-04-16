# pytest-fahhh

[![CI](https://github.com/samiashi/pytest-fahhh/actions/workflows/ci.yml/badge.svg)](https://github.com/samiashi/pytest-fahhh/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/pytest-fahhh.svg)](https://pypi.org/project/pytest-fahhh/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

`pytest-fahhh` is a tiny `pytest` plugin that plays a bundled `fahhh.mp3` whenever a test fails.

Install it, keep running `pytest` like normal, and every failed test call gets the meme sound effect.

## Install

If your project uses `uv`:

```bash
uv add --dev pytest-fahhh
```

If your project uses `pip`:

```bash
pip install pytest-fahhh
```

Pytest auto-discovers the plugin through the `pytest11` entry point, so there is no extra setup after install.
The important part is that `pytest-fahhh` must be installed in the same environment where you run `pytest`.

## Usage

Run `pytest` as usual:

```bash
pytest
```

When a test fails during its call phase, `pytest-fahhh` launches the bundled audio clip in the background.

## Disable It

Disable it for one run:

```bash
pytest --no-fahhh
```

Disable it through the environment:

```bash
PYTEST_FAHHH_DISABLE=1 pytest
```

Disable it in `pytest.ini`:

```ini
[pytest]
fahhh = false
```

## Platform Notes

- macOS: uses `afplay`
- Linux: tries `paplay`, `aplay`, `ffplay`, then `mpg123`
- Other platforms: installs fine, but the plugin currently warns and does nothing because no player command is configured yet

## Local Development

```bash
uv sync
make lint
make test
```

Run the intentional sound demo:

```bash
make demo-sound
```
