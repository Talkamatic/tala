# AGENTS.md
# Guide for agentic coding tools in this repo.

## Environment
- Always use the Python 3.11 virtual environment at `~/python_3_11_environment`.
- Activate it before any command:
  - `source ~/python_3_11_environment/bin/activate`

## Project snapshot
- Package name: `tala` (Python 3.11).
- Tests use `pytest` with class-style tests in `tala/**/test`.
- Lint/format: `flake8` and `yapf` configured in `setup.cfg`.
- Dev tools listed in `requirements-dev.txt`.

## Install / setup
- Install runtime deps:
  - `python -m pip install -e .`
- Install dev deps:
  - `python -m pip install -r requirements-dev.txt`

## Build
- Build sdist/wheel:
  - `python -m build`

## Lint
- Flake8 (configured in `setup.cfg`, 120 col limit):
  - `python -m flake8 tala`
- Pylint (available, no explicit config):
  - `python -m pylint tala`

## Format
- YAPF (configured in `setup.cfg`):
  - `python -m yapf -i path/to/file.py`
  - `python -m yapf -ir tala`

## Tests
- Run all tests:
  - `python -m pytest`
- Run tests in a module:
  - `python -m pytest tala/utils/test/test_requestor.py`
- Run a single test case:
  - `python -m pytest tala/utils/test/test_requestor.py::TestGPTRequest::test_basic_call`
- Run by keyword expression:
  - `python -m pytest -k requestor`

## Pytest details
- Config file: `pytest.ini` (excludes `tala/ddds`).
- Tests commonly use class fixtures (`setup_class`) and pytest fixtures.

## Code style guidelines

### Imports
- Group imports in this order: standard library, third-party, local `tala.*`.
- Keep one import per line unless a short `from ... import ...` list is clearer.
- Prefer absolute imports (e.g., `from tala.utils.func import getenv`).

### Formatting
- Max line length: 120.
- YAPF is the formatter; do not reformat with a different tool.
- Keep dicts and lists readable; existing code often expands large literals.
- Avoid trailing whitespace and keep blank lines between top-level defs.

### Naming
- Classes: `CapWords` (e.g., `GPTRequest`).
- Functions/variables: `snake_case`.
- Constants: `UPPER_CASE` (module-level defaults/timeouts).
- Private/internal: prefix with `_` when not part of public API.

### Types
- The codebase is largely untyped; avoid adding type hints unless helpful
  and consistent with nearby code.
- If you add type hints, keep them minimal and local (function args/return).

### Error handling
- Prefer specific exception types; custom exceptions live near use sites.
- When interacting with external services, log context and raise meaningful
  errors (see `tala/utils/requestor.py`).
- Broad `except Exception` exists in legacy paths; if you touch that code,
  consider tightening to specific exceptions when safe.
- Prefer duck-typing over explicit `isinstance` checks in new code.

### Logging
- Use structured logging via `structlog` (`tala/utils/func.py`).
- Use `setup_logger(__name__)` and log with context (kwargs).
- Avoid logging large session fields directly; redaction is centralized.

### Public API surface
- `tala/__init__.py` exposes package-level names; keep it stable.
- New modules should live under the relevant subpackage (`ddd`, `model`,
  `utils`, `log`, `service`).

### Tests
- Tests are in `tala/**/test` or `tala/**/test/**.py`.
- Use pytest-style `assert` with clear error messages.
- Prefer small, deterministic tests; patch external calls.

### Data and files
- XML/DDD assets live under `tala/ddd` and are packaged via `pyproject.toml`.
- Avoid touching `tala/ddds` in tests; it is excluded from pytest traversal.

## Repository-specific notes
- No Cursor rules were found in `.cursor/rules/` or `.cursorrules`.
- No Copilot instructions were found in `.github/copilot-instructions.md`.

## Commit messages
- Header: max 50 characters.
- Body: 4-8 lines, each max 72 characters.
- Body should be 4-8 lines of continuous prose (no bullets). It must
  explain: 1) what was missing or risky before, 2) why this needed to
  change, and 3) what the change did to address it. Use complete
  sentences and keep lines under 72 characters.
- Avoid blank lines in commit message bodies.
- Prefix bug fix headers with `FIX:` and include the task number.

## Gerrit workflow
- This repo uses Gerrit for code review.
- NEVER push to `origin/master`.
- Only push to `refs/for/master`.
- If you need to update the most recent commit, it is safe to use
  `git commit --amend`.
- To preserve an existing Change-Id when amending, use
  `git commit --amend --no-edit`.
- Never push to `master` (any remote) or `azure-production/master`.
- Agentic tools must not run `git push` commands. Ask a human to push.

## When in doubt
- Follow existing patterns in nearby files.
- Keep edits small and focused; avoid broad reformatting.
