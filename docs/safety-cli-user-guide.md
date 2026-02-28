# Safety CLI Developer User Guide

**Version 3.8.0b1** | Python Dependency Vulnerability Scanner

Safety CLI detects packages with known vulnerabilities and malicious packages. It scans local projects, CI/CD pipelines, and entire developer machines. Published on PyPI as `safety`.

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Authentication](#authentication)
3. [Global Options](#global-options)
4. [Commands Reference](#commands-reference)
   - [scan (Primary)](#safety-scan)
   - [system-scan (Beta)](#safety-system-scan)
   - [check (Legacy)](#safety-check)
   - [auth](#safety-auth)
   - [firewall](#safety-firewall)
   - [init](#safety-init)
   - [codebase](#safety-codebase)
   - [Tool Interceptors](#tool-interceptors)
   - [configure](#safety-configure)
   - [generate](#safety-generate)
   - [validate](#safety-validate)
   - [license (Legacy)](#safety-license)
   - [check-updates](#safety-check-updates)
5. [Output Formats](#output-formats)
6. [Configuration Files](#configuration-files)
7. [Environment Variables](#environment-variables)
8. [TLS & Proxy Configuration](#tls--proxy-configuration)
9. [Policy-Based Vulnerability Management](#policy-based-vulnerability-management)
10. [Exit Codes](#exit-codes)
11. [CI/CD Integration](#cicd-integration)
12. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Install from PyPI

```bash
pip install safety
```

### Quick Start

```bash
# Interactive setup wizard (recommended for first-time users)
safety init

# Or authenticate directly
safety auth login

# Scan your project
safety scan --target .

# Check a requirements file (legacy)
safety check -r requirements.txt
```

### Environment Setup (Development)

```bash
# Uses hatch + uv
hatch env create              # Create virtual environment at .venv/
hatch env remove              # Reset environment
```

---

## Authentication

Safety CLI supports multiple authentication methods. Most commands require authentication to access the Safety vulnerability database.

### Method 1: Browser-Based OAuth2 (Recommended)

```bash
safety auth login
```

Opens your default browser for OAuth2 PKCE authentication. Tokens are stored in `~/.safety/auth.ini`.

### Method 2: Headless Login

```bash
safety auth login --headless
```

Displays a URL to copy/paste into any browser. Useful for remote/SSH sessions.

### Method 3: API Key (CI/CD)

```bash
# Via environment variable (recommended for CI)
export SAFETY_API_KEY=your-api-key-here
safety scan

# Via command-line flag
safety scan --key your-api-key-here
```

### Method 4: Register a New Account

```bash
safety auth register
```

Creates a new Safety account via browser.

### Method 5: MDM Enrollment (Managed Devices)

```bash
# Enroll with a key provided by your MDM administrator
safety auth enroll YOUR_ENROLLMENT_KEY

# Via environment variable
export SAFETY_ENROLLMENT_KEY=sfek_...
safety auth enroll

# Override auto-detected machine identity
safety auth enroll YOUR_KEY --machine-id custom-machine-id

# Force re-enrollment
safety auth enroll YOUR_KEY --force
```

Enrolls the machine with the Safety Platform for MDM-managed scanning. The enrollment key must match the format `sfek_` followed by 43 base64url characters (alphanumeric, `-`, or `_`). Machine identity is auto-detected from platform-specific hardware IDs but can be overridden via `--machine-id` or the `SAFETY_MACHINE_ID` environment variable.

On success, a machine token is stored in `~/.safety/auth.ini` under the `[machine]` section.

### Token Lifecycle

| Token | Lifespan | Purpose |
|-------|----------|---------|
| Access Token | ~1 hour | Authorization for API calls (JWT) |
| ID Token | ~1 hour | User identity claims (JWT) |
| Refresh Token | ~30 days | Obtain new access/id tokens silently |

Tokens are automatically refreshed when expired. If the refresh token also expires, you'll need to `safety auth login` again.

---

## Global Options

These flags are available on all Safety CLI commands:

| Flag | Description | Environment Variable |
|------|-------------|---------------------|
| `--version` | Show version and exit | — |
| `--debug` | Enable debug logging | — |
| `--disable-optional-telemetry` | Disable analytics telemetry | — |
| `--key <API_KEY>` | API key for authentication | `SAFETY_API_KEY` |
| `--stage <STAGE>` | Dev/staging/production stage | `SAFETY_STAGE` |
| `--proxy-protocol <http\|https>` | Proxy protocol | — |
| `--proxy-host <HOST>` | Proxy hostname | — |
| `--proxy-port <PORT>` | Proxy port number | — |

---

## Commands Reference

### `safety scan`

**Status: PRIMARY (Recommended)**

The main vulnerability scanning command. Scans project directories for dependency files and checks them against the Safety vulnerability database.

```bash
safety scan [OPTIONS]
```

#### Key Options

| Option | Description | Default |
|--------|-------------|---------|
| `--target <PATH>` | Directory to scan | Current directory |
| `--output <FORMAT>` | Output format: `screen`, `json`, `html`, `spdx`, `spdx@2.3`, `spdx@2.2`, `none` | `screen` |
| `--policy-file <PATH>` | Path to `.safety-policy.yml` | Auto-discovered |
| `--save-as <FORMAT> <PATH>` | Save report to file (e.g., `--save-as json report.json`) | — |
| `--apply-fixes` | Auto-apply remediation fixes | `false` |
| `--detailed-output` | Show full advisory information | `false` |
| `--filter <KEYS>` | Filter JSON output by specific keys | — |
| `--use-server-matching` | Use server-side version matching | `false` |

#### Examples

```bash
# Basic project scan
safety scan --target /path/to/project

# Scan with JSON output saved to file
safety scan --output json --save-as json report.json

# Scan with SBOM output (SPDX 2.3)
safety scan --output spdx@2.3

# Scan and auto-fix vulnerabilities
safety scan --apply-fixes

# Scan with custom policy
safety scan --policy-file /path/to/.safety-policy.yml
```

---

### `safety system-scan`

**Status: BETA**

Scans an entire developer machine to discover Python runtimes, virtual environments, installed packages, and development tools. Provides a comprehensive software supply chain inventory.

```bash
safety system-scan run [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--background` / `-b` | Run scan in background (detached process) | `false` |

**Advanced options** (hidden — subject to change):

| Option | Description | Default |
|--------|-------------|---------|
| `--sink <TYPE>` | Output destination: `platform` or `jsonl` | `platform` |
| `--platform-url <URL>` | Safety Platform API endpoint | Default platform URL |
| `--jsonl-path <PATH>` | Directory for JSONL output files | `~/.safety/` |

#### Execution Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Interactive** | TTY terminal, not CI | Rich TUI with live updates, auto-exits 10s after completion |
| **Non-Interactive** | Piped/redirected output, CI | Silent execution, exit code only |
| **Background** | `--background` flag | Detached subprocess, parent exits immediately |

#### What It Discovers

- **Execution Context**: Machine ID, hostname, OS info, architecture
- **Python Runtimes**: All Python installations (system, homebrew, pyenv, etc.)
- **Virtual Environments**: venv, conda, poetry, uv, pipenv environments
- **Dependencies**: All installed packages with versions and PURLs
- **Tools**: Package managers (pip, poetry, uv), VCS (git), containers (docker), IDEs, AI tools

#### Discovery Sources

1. **PATH Source**: Scans `$PATH` for executables
2. **Known Paths Source**: Platform-specific installation directories (e.g., `/opt/homebrew`, `/Library/Frameworks/Python.framework`)
3. **Home Source**: Recursive marker-driven scan from `$HOME` (max depth 5), detecting `pyvenv.cfg`, `pyproject.toml`, `requirements.txt`, etc.

#### Examples

```bash
# Interactive scan (sends results to Safety Platform)
safety system-scan run

# Background scan
safety system-scan run --background

# Save results locally as JSONL
safety system-scan run --sink jsonl --jsonl-path ./scan-results/
```

---

### `safety check`

**Status: DEPRECATED (Legacy — unsupported after June 1, 2024). Use `safety scan` instead.**

Checks a requirements file or stdin for packages with known vulnerabilities.

```bash
safety check [OPTIONS]
```

#### Key Options

| Option | Description | Default |
|--------|-------------|---------|
| `-r` / `--file <PATH>` | Requirements file to check (can repeat) | — |
| `--stdin` | Read requirements from stdin | `false` |
| `--db <PATH>` | Path to local vulnerability database | Remote DB |
| `-o` / `--output <FORMAT>` | Output format: `screen`, `text`, `json`, `bare`, `html` | `screen` |
| `--json` | Shortcut for `--output json` | — |
| `--bare` | Shortcut for `--output bare` | — |
| `--full-report` | Show all details in output | `false` |
| `-i` / `--ignore <ID>` | Ignore specific vulnerability ID (repeatable) | — |
| `--ignore-unpinned-requirements` | Skip packages without pinned versions | Policy default |
| `--policy-file <PATH>` | Path to `.safety-policy.yml` | Auto-discovered |
| `--exit-code / --continue-on-error` | Exit 64 on vulns / Exit 0 always | `--exit-code` |
| `--cache` | Enable local database caching | `false` |
| `-asu` / `--apply-security-updates` | Apply available security updates | `false` |
| `-asul` / `--auto-security-updates-limit <TYPES>` | Limit update types: `patch`, `minor`, `major` | `patch` |
| `-np` / `--no-prompt` | Don't ask for remediations outside the limit | `false` |
| `--json-output-format <VERSION>` | JSON schema version (`0.5` or `1.1`) | `1.1` |
| `--save-json <PATH>` | Save JSON report to file | — |
| `--save-html <PATH>` | Save HTML report to file | — |
| `--audit-and-monitor` / `--disable-audit-and-monitor` | Send results to Safety Platform | `true` |
| `--project <NAME>` | Project name for platform tracking | — |

#### Examples

```bash
# Check a requirements file
safety check -r requirements.txt

# Check multiple files
safety check -r requirements.txt -r requirements-dev.txt

# Pipe from pip freeze
pip freeze | safety check --stdin

# Ignore specific vulnerabilities
safety check -r requirements.txt -i 12345 -i 67890

# JSON output for CI
safety check -r requirements.txt --json

# Auto-apply patch-level security updates
safety check -r requirements.txt --apply-security-updates --auto-security-updates-limit patch
```

---

### `safety auth`

Authentication management commands.

#### `safety auth login`

```bash
safety auth login [--headless]
```

Authenticate via browser-based OAuth2 PKCE flow. Use `--headless` for environments without a browser.

#### `safety auth logout`

```bash
safety auth logout
```

Clear stored authentication tokens.

#### `safety auth register`

```bash
safety auth register
```

Create a new Safety account via browser.

#### `safety auth status`

```bash
safety auth status [--ensure-auth] [--login-timeout <SECONDS>]
```

Check current authentication status. With `--ensure-auth`, blocks until authenticated (useful in scripts). Default login timeout is 600 seconds.

#### `safety auth enroll`

```bash
safety auth enroll [ENROLLMENT_KEY] [--machine-id <ID>] [--force]
```

Enroll this machine with the Safety Platform for MDM-managed scanning.

| Option/Argument | Description | Default | Env Var |
|-----------------|-------------|---------|---------|
| `ENROLLMENT_KEY` (positional) | Enrollment key from MDM administrator (`sfek_` + 43 base64url chars) | — | `SAFETY_ENROLLMENT_KEY` |
| `--machine-id` | Override auto-detected machine identity | Auto-detected | `SAFETY_MACHINE_ID` |
| `--force` | Force re-enrollment even if already enrolled | `false` | — |

**Machine ID resolution order:** `--machine-id` flag > `SAFETY_MACHINE_ID` env var > platform-specific hardware ID. (During enrollment, any previously persisted machine ID is skipped to avoid circular dependency.)

**Enrollment-specific exit codes:**

| Code | Meaning |
|------|---------|
| `73` | Enrollment failed (permanent — invalid key, 401, 409) |
| `74` | Cannot determine machine identity from any source |
| `75` | Enrollment failed (transient — 5xx, network error; MDM orchestrators should retry) |

---

### `safety firewall`

**Status: BETA**

Protects package installations by intercepting package manager commands and validating packages against the Safety threat database before installation.

#### `safety firewall init`

```bash
safety firewall init [--tool <pip|poetry|uv|npm>] ...
```

The `--tool` option is repeatable (e.g., `--tool pip --tool poetry`). If omitted, all supported tools are configured.

Install package manager wrappers. Creates shell aliases (Unix) or registry entries (Windows) that route package manager commands through Safety's validation.

**What happens on Unix/macOS:**
1. Creates `~/.safety/.safety_profile` with aliases
2. Adds source line to `~/.bashrc`, `~/.zshrc`, etc.
3. After install, run `source ~/.safety/.safety_profile` or restart your terminal

**What happens on Windows:**
1. Adds AutoRun entry to `HKCU\Software\Microsoft\Command Processor`
2. Restart Command Prompt to activate

#### `safety firewall uninstall`

```bash
safety firewall uninstall
```

Remove all firewall interceptors and restore original package manager behavior.

#### How Firewall Works

```
User: pip install requests
        │
        ▼
Shell alias: pip → safety firewall pip
        │
        ▼
Safety validates package against:
  ├─ Known vulnerability database
  ├─ Malicious package registry
  └─ Typosquatting patterns
        │
        ▼
  Safe? ──→ Install proceeds (real pip)
  Risky? ─→ Warning shown, policy-based allow/block
  Malicious? → Installation blocked
```

**Supported Package Managers:**
- `pip` (including pip3, pip3.9, pip3.10, etc.)
- `poetry`
- `uv`
- `npm`

---

### `safety init`

**Status: BETA**

Interactive onboarding wizard that walks through complete Safety setup.

```bash
safety init [DIRECTORY]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `DIRECTORY` | Directory to initialize as a codebase | Current directory |

**Wizard Flow (interactive):**
1. Welcome screen
2. Authentication (login or register)
3. Firewall setup (optional — configure pip/poetry/uv/npm interception)
4. Codebase registration (link to Safety Platform project)
5. Initial vulnerability scan
6. Setup complete with next steps

---

### `safety codebase`

**Status: BETA**

Manage Safety projects and codebases.

#### `safety codebase init`

```bash
safety codebase init [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--name <NAME>` | Codebase name (defaults to git origin, parent dir, or random) | Auto-detected |
| `--link-to <SLUG>` | Link to existing codebase by slug (mutually exclusive with `--name`) | — |
| `--skip-firewall-setup` | Don't enable Firewall protection for this codebase | `false` |
| `--path <PATH>` | Path to the codebase directory | Current directory |

Creates `.safety-project.ini` in the target directory, linking it to a Safety Platform project.

---

### Tool Interceptors

Safety can wrap package manager commands to validate packages before installation.

```bash
# Wrapped pip (validates packages before installing)
safety pip install requests

# Wrapped poetry
safety poetry add django

# Wrapped uv
safety uv pip install flask

# Wrapped npm
safety npm install express
```

These commands pass all arguments through to the real package manager after Safety validates the packages. They're activated automatically when the firewall is installed, but can also be called directly.

---

### `safety configure`

Configure global Safety settings.

```bash
safety configure [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--proxy-protocol <http\|https>` / `-pr` | Proxy protocol (requires `--proxy-host`) | `https` |
| `--proxy-host <HOST>` / `-ph` | Proxy hostname | — |
| `--proxy-port <PORT>` / `-pp` | Proxy port (requires `--proxy-host`) | `80` |
| `--organization-id <ID>` / `-org-id` | Organization ID (requires `--organization-name`) | — |
| `--organization-name <NAME>` / `-org-name` | Organization name (requires `--organization-id`) | — |
| `--stage <STAGE>` / `-stg` | Development stage | `development` |
| `--save-to-system` / `--save-to-user` | Save to system-level config instead of user-level | `--save-to-user` |

Writes settings to `~/.safety/config.ini` (user) or the system config directory (with `--save-to-system`).

---

### `safety generate`

Generate a Safety policy file template.

```bash
safety generate policy_file [--path <OUTPUT_PATH>] [--minimum-cvss-severity <SEVERITY>]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--path` | Directory where the generated file will be saved | Current directory |
| `--minimum-cvss-severity` | Minimum CVSS severity for the policy | `critical` |

Creates a `.safety-policy.yml` template with all available configuration options and documentation comments.

---

### `safety validate`

Validate a Safety policy file.

```bash
safety validate policy_file [VERSION] [--path <POLICY_FILE_PATH>]
```

| Option/Argument | Description | Default |
|-----------------|-------------|---------|
| `VERSION` (optional) | Policy file version to validate against (`3.0` or `2.0`) | — |
| `--path` | Path to the policy file | `.safety-policy.yml` |

Checks that the policy file is syntactically correct and all values are valid. Returns exit code 0 on success, 1 on error.

---

### `safety license`

**Status: DEPRECATED (Legacy)**

Check package licenses against an allow/deny list.

```bash
safety license [OPTIONS]
```

---

### `safety check-updates`

Check if a newer version of Safety CLI is available.

```bash
safety check-updates [--output <FORMAT>]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output format: `screen` or `json` | `screen` |

Requires authentication. Compares installed version against the latest release.

---

## Output Formats

### Format Comparison

| Format | Human | Machine | Color | Use Case |
|--------|-------|---------|-------|----------|
| `screen` | Yes | No | Yes | Interactive terminal (default) |
| `text` | Yes | No | No | Piping, file output, logs |
| `json` | No | Yes | N/A | CI/CD, automation, APIs |
| `bare` | No | Yes | No | Shell scripts (`grep`/`awk`) |
| `html` | Yes | No | Yes | Email reports, archival |
| `spdx` / `spdx@2.3` / `spdx@2.2` | No | Yes | N/A | SBOM compliance (SPDX format) |
| `none` | — | — | — | Suppress output (exit code only) |

**Format availability by command:**
- `safety scan`: `screen`, `json`, `html`, `spdx`, `spdx@2.3`, `spdx@2.2`, `none`
- `safety check`: `screen`, `text`, `json`, `bare`, `html`
- `safety check-updates`: `screen`, `json`

### Screen (Default)

Rich colored terminal output with ASCII art banner, vulnerability tables, remediation guidance, and summary statistics. Dynamically sized to terminal width.

```bash
safety check -r requirements.txt --output screen
```

### Text

Plain text output identical to screen but without ANSI color codes. Fixed at 80 columns.

```bash
safety check -r requirements.txt --output text > report.txt
```

### JSON

Machine-readable JSON output. Two schema versions available:

```bash
# Current schema (v1.1, default)
safety check -r requirements.txt --output json

# Legacy schema (v0.5, for backwards compatibility)
safety check -r requirements.txt --output json --json-output-format 0.5
```

**JSON v1.1 structure:**
```json
{
  "report_meta": {
    "scanned_packages": 42,
    "vulnerabilities_found": 3,
    "vulnerabilities_ignored": 1,
    "severity": {
      "critical": 1, "high": 2, "medium": 0, "low": 0
    }
  },
  "scanned_packages": { ... },
  "affected_packages": { ... },
  "vulnerabilities": [ ... ],
  "ignored_vulnerabilities": [ ... ],
  "remediations": { ... }
}
```

### Bare

Minimal space-separated output — just affected package names. Designed for shell scripting.

```bash
safety check -r requirements.txt --output bare
# Output: django requests
```

```bash
# Example: iterate over vulnerable packages
for pkg in $(safety check -r requirements.txt --output bare); do
  echo "Vulnerable: $pkg"
done
```

### HTML

Complete HTML document with embedded styling for reports and sharing.

```bash
safety check -r requirements.txt --output html > report.html
```

### SPDX (SBOM)

Software Bill of Materials in SPDX JSON format for compliance and supply chain audits.

```bash
# Latest SPDX version
safety scan --output spdx

# Specific SPDX version
safety scan --output spdx@2.3
safety scan --output spdx@2.2
```

### Saving Reports

```bash
# Save via --save-as (scan command, space-separated FORMAT PATH)
safety scan --save-as json report.json
safety scan --save-as html report.html

# Save via legacy flags (check command)
safety check -r requirements.txt --save-json report.json
safety check -r requirements.txt --save-html report.html
```

---

## Configuration Files

### File Locations

```
~/.safety/
├── config.ini                    # Global configuration (TLS, proxy, org)
├── auth.ini                      # OAuth2 tokens (auto-managed)
├── .safety_profile               # Shell aliases (generated by firewall init)
└── 200/
    └── cache.json                # Vulnerability DB cache

<project-root>/
├── .safety-project.ini           # Project ID linkage (generated by init)
└── .safety-policy.yml            # Vulnerability policy rules
```

### config.ini

Global Safety configuration. Located at `~/.safety/config.ini` (user-level) or the system-level directory (platform-specific). System-level takes precedence if it exists.

**System config directories:**
- **macOS:** `/Library/Application Support/.safety/config.ini`
- **Linux:** `/etc/.safety/config.ini`
- **Windows:** `%ALLUSERSPROFILE%\.safety\config.ini`
- Override with `SAFETY_SYSTEM_CONFIG_PATH` environment variable.

```ini
[organization]
id = org-uuid-here
name = My Organization

[host]
stage = development

[settings]
firewall_enabled = True
platform_enabled = True

[tls]
mode = default              # default | system | bundle
ca_bundle = /path/to/ca.crt # Required if mode=bundle

[proxy]
protocol = http             # http | https
host = proxy.example.com
port = 8080
```

### auth.ini

Auto-managed OAuth2 token storage. Do not edit manually.

```ini
[auth]
access_token = eyJ0eXAi...
id_token = eyJ0eXAi...
refresh_token = eRT6x-...
```

**Security note:** Tokens are stored as plaintext. File relies on OS file permissions for protection. The file is located at `~/.safety/auth.ini`.

### .safety-project.ini

Created by `safety init` or `safety codebase init` in a project root. Links the codebase to a Safety Platform project.

```ini
[project]
id = project-uuid-here
```

### .safety-policy.yml

Policy file for vulnerability management. See [Policy-Based Vulnerability Management](#policy-based-vulnerability-management).

---

## Environment Variables

### Core Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SAFETY_API_KEY` | API key for authentication | — |
| `SAFETY_OUTPUT` | Default output format | `screen` |
| `SAFETY_COLOR` | Force color output on/off (`true`/`1` = on, `false`/`0` = off) | Auto-detected |
| `SAFETY_STAGE` | Development stage (dev/staging/production) | — |
| `SAFETY_DB_DIR` | Path to local vulnerability database directory (bypasses auth when set) | — |
| `SAFETY_REQUEST_TIMEOUT` | HTTP request timeout in seconds | `30` |
| `SAFETY_REQUEST_TIMEOUT_EVENTS` | Event/telemetry timeout in seconds | `10.0` |
| `SAFETY_SYSTEM_CONFIG_PATH` | Override config directory path | Platform-specific |

### Enrollment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SAFETY_ENROLLMENT_KEY` | MDM enrollment key for `safety auth enroll` | — |
| `SAFETY_MACHINE_ID` | Override auto-detected machine identity for enrollment | — |

### TLS Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SAFETY_TLS_MODE` | TLS verification mode: `default`, `system`, `bundle` | — |
| `SAFETY_CA_BUNDLE` | Path to custom CA certificate bundle | — |

If `SAFETY_CA_BUNDLE` is set without `SAFETY_TLS_MODE`, mode is inferred as `bundle`.

### Telemetry & Git Override Variables

| Variable | Purpose |
|----------|---------|
| `SAFETY_GIT_ORIGIN` | Override Git origin URL for telemetry |
| `SAFETY_GIT_BRANCH` | Override Git branch name for telemetry |
| `SAFETY_GIT_TAG` | Override Git tag for telemetry |
| `SAFETY_GIT_COMMIT` | Override Git commit SHA for telemetry |
| `SAFETY_GIT_DIRTY` | Override dirty state (`0` = clean, `1` = dirty) |
| `SAFETY_OS_TYPE` | Override OS type for telemetry |
| `SAFETY_OS_DESCRIPTION` | Override OS description for telemetry |
| `SAFETY_OS_RELEASE` | Override OS release for telemetry |
| `SAFETY_SOURCE` | Override Safety source identifier for telemetry |
| `CI` | CI environment detection (set automatically by most CI systems) |

### Package Manager Variables (Set by Firewall)

| Variable | Purpose |
|----------|---------|
| `PIP_INDEX_URL` | Pip index URL (pointed to Safety proxy) |
| `POETRY_HTTP_BASIC_SAFETY_*` | Poetry auth credentials for Safety source |
| `UV_DEFAULT_INDEX` | UV default package index |

---

## TLS & Proxy Configuration

### TLS Modes

#### Default Mode (Most Users)

Uses the `certifi` Python package with Mozilla's CA certificate bundle. Works out of the box.

```bash
# No configuration needed (this is the default)
safety scan
```

#### System Mode (Enterprise)

Uses the operating system's certificate store. Picks up corporate/IT-managed certificates automatically.

```bash
export SAFETY_TLS_MODE=system
safety scan
```

Or in `~/.safety/config.ini`:
```ini
[tls]
mode = system
```

#### Bundle Mode (Custom CA)

Uses a custom CA certificate bundle file. Required for corporate proxies with MITM inspection or self-signed certificates.

```bash
export SAFETY_TLS_MODE=bundle
export SAFETY_CA_BUNDLE=/etc/ssl/certs/company-ca.pem
safety scan
```

Or in `~/.safety/config.ini`:
```ini
[tls]
mode = bundle
ca_bundle = /etc/ssl/certs/company-ca.pem
```

The bundle file must be:
- PEM format
- An absolute path
- Readable by the Safety process

### TLS Configuration Priority

1. CLI arguments (highest)
2. Environment variables
3. `config.ini` file
4. Default (certifi bundle)

### Proxy Configuration

Configure via `config.ini` (environment variables not yet supported):

```ini
[proxy]
protocol = https
host = proxy.corp.example.com
port = 3128
```

Or via CLI flags:

```bash
safety scan --proxy-protocol https --proxy-host proxy.corp.example.com --proxy-port 3128
```

### Combined Example (Corporate Environment)

```ini
# ~/.safety/config.ini
[tls]
mode = bundle
ca_bundle = /etc/ssl/certs/company-ca.pem

[proxy]
protocol = https
host = proxy.internal.corp
port = 3128
```

---

## Policy-Based Vulnerability Management

The `.safety-policy.yml` file controls how Safety handles vulnerabilities. Place it in your project root or specify with `--policy-file`.

### Generate a Template

```bash
safety generate policy_file --path .safety-policy.yml
```

### Full Policy Reference

```yaml
# Project identification
project:
  id: 'project-uuid'

organization:
  id: 'org-uuid'
  name: 'Company Name'

# Security rules
security:
  # Ignore packages without pinned versions (e.g., "django" vs "django==3.2")
  ignore-unpinned-requirements: true

  # CVSS severity threshold (0-10)
  # 0: Report all (default)
  # 4: Skip LOW severity
  # 7: Only report HIGH and CRITICAL
  # 9: Only report CRITICAL
  ignore-cvss-severity-below: 0

  # How to handle vulns with unknown/missing CVSS scores
  ignore-cvss-unknown-severity: false

  # Specific vulnerabilities to ignore
  ignore-vulnerabilities:
    12345:
      reason: "We use a workaround for this issue"
      expires: '2024-12-31'    # ISO-8601 date — ignore expires after this
    25853:
      reason: "Not applicable to our use case"

  # Don't fail builds when vulnerabilities are found
  continue-on-vulnerability-error: false

# Automatic security update limits
security-updates:
  auto-security-updates-limit:
    - patch    # Allow 1.0.0 → 1.0.1
    # - minor  # Allow 1.0.0 → 1.1.0
    # - major  # Allow 1.0.0 → 2.0.0

# GitHub alert integration
alert:
  security:
    github-issue:
      ignore-cvss-severity-below: 6
      label-severity: true
      labels: [security, vulnerability]
      assignees: [github-username]
      issue-prefix: "[PyUp] "

    github-pr:
      ignore-cvss-severity-below: 6
      branch: 'main'
      branch-prefix: 'pyup/'
      pr-prefix: '[PyUp] '
      label-severity: true
      labels: [security]
      assignees: [github-username]
```

### Validate Your Policy

```bash
safety validate policy_file --path .safety-policy.yml
```

---

## Exit Codes

| Code | Constant | Meaning |
|------|----------|---------|
| `0` | Success | No vulnerabilities found / command succeeded |
| `1` | General Error | Unspecified error |
| `64` | Vulnerabilities Found | Packages with known vulnerabilities detected |
| `65` | Invalid Auth | Authentication credentials are invalid or expired |
| `66` | Rate Limited | API rate limit exceeded |
| `67` | Cannot Load DB | Cannot load local vulnerability database |
| `68` | Cannot Fetch DB | Cannot download vulnerability database from server |
| `69` | Malformed DB | Vulnerability database is corrupted |
| `70` | Invalid Report | Report generation failed |
| `71` | Invalid Requirement | Cannot parse a requirement line |
| `72` | Email Not Verified | User email needs verification |
| `73` | Enrollment Failed | Machine enrollment failed (permanent — invalid key, unauthorized, conflict) |
| `74` | Machine ID Unavailable | Cannot determine system machine identity from any source |
| `75` | Enrollment Transient Failure | Machine enrollment failed (transient — 5xx, network error; MDM should retry) |

### Using Exit Codes in CI

```bash
safety check -r requirements.txt
EXIT_CODE=$?

case $EXIT_CODE in
  0)  echo "All clear" ;;
  64) echo "Vulnerabilities found — review report" ;;
  65) echo "Auth failed — check SAFETY_API_KEY" ;;
  *)  echo "Error: exit code $EXIT_CODE" ;;
esac
```

To suppress vulnerability exit codes (always exit 0):
```bash
safety check -r requirements.txt --continue-on-error
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  safety-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Safety
        run: pip install safety

      - name: Run vulnerability scan
        env:
          SAFETY_API_KEY: ${{ secrets.SAFETY_API_KEY }}
        run: |
          safety check -r requirements.txt \
            --output json \
            --policy-file .safety-policy.yml \
            --save-json safety-report.json

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: safety-report
          path: safety-report.json
```

### GitLab CI

```yaml
safety-scan:
  image: python:3.11
  script:
    - pip install safety
    - safety check -r requirements.txt --output json --save-json report.json
  variables:
    SAFETY_API_KEY: $SAFETY_API_KEY
  artifacts:
    paths:
      - report.json
    when: always
```

### Pre-Commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: safety-check
        name: Safety vulnerability check
        entry: safety check -r requirements.txt --continue-on-error
        language: system
        pass_filenames: false
        always_run: true
```

### CI/CD Best Practices

- Use `SAFETY_API_KEY` environment variable (not browser login)
- Use `--output json` for programmatic parsing
- Use `--save-as` or `--save-json` for report archival
- Use `--disable-optional-telemetry` for privacy
- Use `--policy-file` for consistent rules across environments
- Use exit codes (0/64) for pipeline pass/fail decisions

---

## Troubleshooting

### Common Issues

#### "Invalid authentication token"

```bash
# Clear and re-authenticate
safety auth logout
safety auth login
```

Or check that `SAFETY_API_KEY` is set correctly in your environment.

#### "No available ports" during login

All dynamic ports are in use. Use headless login:
```bash
safety auth login --headless
```

#### "State mismatch" error during login

The browser callback was intercepted or replayed. Retry:
```bash
safety auth login
```

Check your network security (VPN, proxy, firewall) and system clock accuracy.

#### Token refresh failures (401 errors)

Tokens may have expired beyond refresh window:
```bash
safety auth logout
safety auth login
```

#### TLS/Certificate errors

If behind a corporate proxy:
```bash
# Try system certificates first
export SAFETY_TLS_MODE=system
safety scan

# Or provide your corporate CA bundle
export SAFETY_TLS_MODE=bundle
export SAFETY_CA_BUNDLE=/path/to/corporate-ca.pem
safety scan
```

#### Firewall not intercepting commands

After `safety firewall init`, you must restart your terminal or source the profile:
```bash
source ~/.safety/.safety_profile
```

Verify aliases are active:
```bash
which pip  # Should show "pip: aliased to safety firewall pip"
```

### Debug Logging

Enable verbose logging for any command:
```bash
safety --debug scan --target .
```

### Getting Help

```bash
safety --help                    # Global help
safety scan --help               # Command-specific help
safety auth --help               # Subcommand group help
```

---

## Command Quick Reference

| Command | Status | Auth Required | Primary Use |
|---------|--------|---------------|-------------|
| `safety scan` | **Primary** | Yes | Project vulnerability scanning |
| `safety system-scan run` | Beta | Yes | Machine-wide inventory |
| `safety check` | Deprecated | Optional | Legacy vulnerability check |
| `safety auth login` | Active | No | Authenticate |
| `safety auth logout` | Active | No | Clear tokens |
| `safety auth register` | Active | No | Create account |
| `safety auth status` | Active | No | Check auth |
| `safety auth enroll` | Active | No | MDM machine enrollment |
| `safety firewall init` | Beta | No | Install package wrappers |
| `safety firewall uninstall` | Beta | No | Remove package wrappers |
| `safety init` | Beta | Interactive | Guided setup wizard |
| `safety codebase init` | Beta | Yes | Register project |
| `safety configure` | Active | No | Edit global config |
| `safety generate policy_file` | Active | No | Create policy template |
| `safety validate policy_file` | Active | No | Validate policy file |
| `safety check-updates` | Active | Yes | Check for CLI updates |
| `safety pip/uv/poetry/npm` | Active | Yes | Wrapped package managers |
