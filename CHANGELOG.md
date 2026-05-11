# Change Log
This changelog is curated and focuses on major changes. For the full historical
record before 12.0.0, see CHANGELOG.legacy.md.

## Unreleased
- CLI: remove the deprecated multi-command `tala` interface; `tala-interact` is
  the only supported CLI entry point.
- Docs: update CLI documentation to cover `tala-interact` only.
- Changelog: archive historical entries in `CHANGELOG.legacy.md`.
- Service: remove unused legacy constants module.
- Cleanup: drop unused empty packages under `tala/service` and `bin`.

## Highlights since 12.0.0 (major changes only)

### 29.x-30.x (2026)
- Requestor improvements: caching, timeouts, reasoning effort, content-filter
  handling, JSON repair retry, and improved logging.
- JSON:API hardening, DDD JSON/XML parity, and JSON bundle loading.
- Deprecated APIs and semantic logic removed; move module refactors and legacy
  parsing fixes.

### 27.x-28.x (2025)
- NLG refactor and move to `tala.nlg`.
- User rates DB extended with dialogue IDs and author notification parameters.

### 25.x-26.x (2025)
- New JSON serialization format for DDD-related models; `<once>` plan item
  introduced.
- SSE client supports multiple sessions; NLG enhancements for move sequences
  and slots.

### 23.x-24.x (2025)
- Packaging moved to `pyproject.toml`.
- Updated SSE streamer endpoint configuration.

### 21.x-22.x (2025)
- Streaming test coverage and MQTT streaming fixes; stream checking added then
  removed for performance.
- NLG added to Tala and expanded; lightweight SSE client introduced.

### 19.x-20.x (2024)
- Interaction testing overhaul: new framework layout and endurance testing
  removed.
- MQTT client updates including pronunciation lexicons and timing constraints.

### 17.x-18.x (2024)
- Quota DB tooling: table handler, user rates tracking, and author/offer quota
  updates.
- Python 3.11 support and publish action updates.

### 15.x-16.x (2023-2024)
- New JSON-based interaction tests and fixes for interpretation output.
- TDM-specific functionality moved out of Tala; model class renames and HTTP
  formatting simplification.
- Interaction tester improvements: device id, neural parameter, and logging
  defaults.

### 14.x (2023)
- Migration to GitHub with PyPI publish workflow.
- Deprecation of non-pythonic names and migration toward properties.
- Interaction test generation updated for TDM start behavior changes.

### 12.x-13.x (2022-2023, from legacy tags)
- JSON support for DDDs and ODBs: JSON parsing, ODB serialization to JSON, and
  on-demand JSON DDD loading.
- TIS sessions and payloads stored as JSON (multiple betas in 13.2.x).
- Configurable HTTP service timeout and removal of the libmagic dependency.
