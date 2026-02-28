# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

For detailed architecture, module guide, data flows, and navigation, see [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).

**IMPORTANT**: If any code change invalidates details in this file or in [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md), you **MUST** update them to stay in sync with the code.

## Project Overview

Safety CLI (v3.8.0b1) by SafetyCLI scans dependencies for known vulnerabilities and licenses. It also includes a package firewall with typosquatting/malicious package detection. Source: `https://github.com/pyupio/safety`.

## Build & Development Commands

**Build system**: Hatch with hatchling backend, uv installer. Default env targets Python 3.9.

| Task | Command |
|------|---------|
| Run all tests | `pytest tests/` (with .venv active) |
| Run all tests (container) | `hatch run test.py3.9:test` (requires container tooling — `test` env uses `type = "container"`) |
| Run single test | `pytest tests/auth/test_enroll.py::TestClass::test_method -v` |
| Run tests by marker | `pytest -m unit tests/` or `pytest -m integration tests/` |
| Run tests by name pattern | `pytest -k "test_name_pattern" tests/` |
| Lint (check) | `ruff check .` |
| Lint (fix) | `ruff check --fix .` |
| Format (check) | `ruff format --check --diff .` |
| Format (apply) | `ruff format .` |
| Type check | `hatch run lint:typing` (pyright — `[tool.pyright]` config scopes to `safety/scan/` only) |
| All lint checks | `hatch run lint:all` |
| Build | `hatch build --target wheel --target sdist` |
| Version bump | `hatch run bump` (stable) or `hatch run beta-bump` (beta) |
| Reset hatch env | `hatch env remove && hatch env create` |

## Architecture

### CLI Framework
Typer (on Click). Entry point: `safety.cli:cli`. Sub-apps registered as Typer apps:
- `init_app` — `safety init`
- `scan_project_app` — `safety scan` project scanning
- `system_scan_app` — `safety system-scan` full-machine scanning (beta)
- `codebase_app` — codebase management
- `auth_app` — OAuth2 login, API key, MDM enrollment
- `firewall_app` — `safety pip/uv/poetry` package install interception
- `cli_app` — `check-updates` command

Registered directly as a Click group (not a Typer app, deprecated):
- `alert` — GitHub alert generation (PRs/issues)

Registered separately (not a sub-app — uses `auto_register_tools` directly on the CLI group):
- `tool_commands` — tool wrapper commands for pip, uv, poetry, npm

### Central Context Object
`SafetyCLI` dataclass (`safety/models/obj.py`) — passed through Typer contexts. Holds auth state, telemetry, config, event bus, and feature flags.

### Authentication (Three Paths)
1. **OAuth2** — interactive browser login (`safety/auth/main.py`)
2. **API key** — `--key` flag or `SAFETY_API_KEY` env var
3. **Machine token** — MDM enrollment for managed devices (`safety/auth/enrollment.py`)

### HTTP Client
`SafetyPlatformClient` (`safety/platform/client.py`) wraps `httpx.Client` with:
- `@parse_response` decorator — retries (tenacity), status code handling, error mapping
- TLS fallback (certifi -> system trust store)
- Proxy support

### Scanning Architecture
- **Project scan** (`safety/scan/`): `FileFinder` discovers dependency files → ecosystem handlers process them → checks against vulnerability DB
- **System scan** (`safety/system_scan/`): Pipeline with stages, detectors (runtimes, environments, dependencies, tools, execution contexts), sources, and sinks (JSONL, platform API)

### Event System
Event bus (`safety/events/event_bus/`) with typed events. Commands use `@notify` decorator (`safety/decorators.py`) to emit events. Handlers in `safety/events/handlers/`.

### Error Handling
Two separate exception base classes in `safety/errors.py`, both inheriting from `Exception`:
- `SafetyError` — the active hierarchy with all concrete subclasses (MalformedDatabase, DatabaseFetchError, EnrollmentError, etc.). Each has `get_exit_code()`.
- `SafetyException` — legacy catch-all wrapper with zero subclasses. Used in `safety/error_handlers.py` to wrap unexpected exceptions.

Commands wrapped with `@handle_cmd_exception` decorator (`safety/error_handlers.py`).

### Configuration Resolution (highest to lowest priority)
1. Environment variables (`SAFETY_` prefix)
2. Config file (`~/.safety/config.ini` or system-level)
3. Enum defaults (`URLSettings` in `safety/constants.py`)

## Testing

**Framework**: pytest with strict markers. Tests mirror source directory structure.

**Markers**: `unit`, `basic`, `integration`, `slow`, `windows_only`, `unix_only`, `linux`, `darwin`

**Patterns**: Mix of `unittest.TestCase` classes and pytest-style. Uses `click.testing.CliRunner` for CLI tests, `unittest.mock.patch`/`Mock`/`MagicMock` for mocking. Test data in `tests/resources.py` and `tests/test_db/`.

**CI test matrix**: Python 3.9–3.14, with pydantic and typer/click version variants. Matrix generated from pyproject.toml via `.github/scripts/matrix.py`.

## Code Style

- **Formatter/Linter**: Ruff (using defaults — no ruff config in pyproject.toml)
- **Type checker**: Pyright (`[tool.pyright]` config scopes `include` to `safety/scan/` only)
- **Min Python**: 3.9
- **Commits**: Conventional Commits enforced via commitizen (`<type>(<scope>): <description>`)

## Quality Gates — Mandatory Before Ending a Session

**Run `/review-changes` before every commit.** It runs lint, format, type check, and related tests on changed files. Do not commit or mark work as done without passing. See `.claude/commands/review-changes.md` for full details.

**Skills** (auto-loaded based on context):
- `/capture-skills` → Run at the end of every session to extract learnings into skills, AGENTS.md, or templates

## Key Dependencies

**Core**:
`Authlib>=1.2.0` (OAuth2), `Click>=8.0.2`, `dparse>=0.6.4` (dependency parsing), `filelock>=3.16.1,<4.0`, `httpx`, `jinja2>=3.1.0` (templates), `marshmallow>=3.15.0` (marked for removal), `nltk>=3.9` (typosquatting detection), `packaging>=21.0`, `pydantic>=2.6.0`, `ruamel.yaml>=0.17.21`, `safety-schemas==0.0.16`, `tenacity>=8.1.0` (retries), `typer>=0.16.0`, `typing-extensions>=4.7.1`, `tomlkit`, `certifi`

**Conditional**: `tomli` (Python <3.11), `truststore>=0.10.4` (Python >=3.10)

**Optional extras**: `[github]` (pygithub), `[gitlab]` (python-gitlab), `[spdx]` (spdx-tools)

## CI/CD

- **CI** (`.github/workflows/ci.yml`): validate-commits (commitizen) → lint (ruff + pyright on changed files) → matrix generation → test across Python versions
- **CD** (`.github/workflows/cd.yml`): triggers on version tags → CI → build (package + PyApp binaries) → GitHub Release → PyPI publish
- **PR builds** (`build.yml`, `pr.yml`, `pr-comment.yml`): branch/PR-level build and feedback
- **Version bumping** (`bump.yml`): automated version bump workflow
- Binary distribution via PyApp (Rust-based) for Linux, macOS, Windows
- Code signing: cosign/sigstore for binary attestation, Apple notarization (macOS), Azure Trusted Signing (Windows)

## Agent Workflow Learnings

1. **Run `/capture-skills` before closing every session**: Review the session for confusing patterns, novel solutions, high-token-cost explorations, user corrections, or new architectural decisions. Capture them as skill updates, new skills, or AGENTS.md entries. This prevents the team from re-learning the same lessons across sessions.
