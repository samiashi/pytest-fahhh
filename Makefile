UV ?= uv
TOX ?= $(UV) tool run --with tox-uv tox
PYTHON_VERSIONS = 3.9 3.10 3.11 3.12 3.13 3.14

.PHONY: help sync lock pythons lint format test tox demo-sound build check-dist publish clean

help:
	@printf "Targets:\n"
	@printf "  make sync    - create/update the uv-managed project environment\n"
	@printf "  make lock    - refresh uv.lock without syncing the environment\n"
	@printf "  make lint    - run ruff check and ruff format --check\n"
	@printf "  make format  - fix imports and format the repository with ruff\n"
	@printf "  make pythons - install CPython 3.9 through 3.14 via uv\n"
	@printf "  make test    - run the tox test matrix for CPython 3.9 through 3.14\n"
	@printf "  make tox     - run tox with custom args, e.g. make tox ARGS='-e py314'\n"
	@printf "  make demo-sound - run the intentional failing sound demo test\n"
	@printf "  make build   - build sdist and wheel into dist/\n"
	@printf "  make check-dist - validate built artifacts with twine metadata checks\n"
	@printf "  make publish - upload the built distributions with uv publish\n"
	@printf "  make clean   - remove local build artifacts\n"

sync:
	$(UV) sync --group dev

lock:
	$(UV) lock

lint: sync
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format: sync
	$(UV) run ruff check --select I --fix .
	$(UV) run ruff format .

pythons:
	$(UV) python install $(PYTHON_VERSIONS)

test: pythons
	$(TOX) run

tox: pythons
	$(TOX) run $(ARGS)

demo-sound: sync
	$(UV) run pytest -m manual_sound_demo -s tests/test_manual_sound_demo.py || true

build:
	$(UV) build

check-dist: build
	$(UV) tool run twine check dist/*

publish:
	$(UV) publish

clean:
	rm -rf .venv .pytest_cache .ruff_cache .tox build dist src/pytest_fahhh.egg-info tests/__pycache__
