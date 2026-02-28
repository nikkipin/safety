# Review Changes Command

Run quality checks on only the files that have changed (staged + unstaged), mirroring the CI lint job.

## Checks Performed

1. **Lint + Format** — `hatch run lint:style` (ruff check + ruff format --check --diff)
2. **Type check** — `hatch run lint:typing` (pyright, scoped to `safety/scan/` per `[tool.pyright]`)
3. **Related tests** — discover and run tests for changed files (unless `--no-tests`)

Or combined: `hatch run lint:all <files>` runs lint + format + type check in one step.

## Workflow

1. **Identify changed Python files**:
   ```bash
   git diff --name-only HEAD
   git diff --name-only --cached
   ```
   Filter to `.py` files that still exist on disk. Deduplicate.

2. **Run targeted checks** (on changed files only):
   ```bash
   # Runs ruff check + ruff format --check --diff + pyright
   hatch run lint:all <changed_py_files>
   ```
   This matches what CI does: `hatch run lint:all ${FILES}`.

3. **Discover and run related tests** (default behavior):
   See Related Test Discovery below. Skip with `--no-tests`.

4. **Report results**:
   - List files checked
   - Show any issues found per category
   - Suggest fixes (but do NOT auto-fix unless `--fix` is passed)

## Rules

- **You own every error on files you touch.** Never dismiss lint/type errors as pre-existing — if your changes touch a file, that file must be clean before you commit.
- **Do not commit or mark work as done without passing these checks.** If checks fail, fix the issues before proceeding.

## Arguments

`$ARGUMENTS` - Optional flags:
- `--fix` - Auto-fix formatting and lint issues before checking
- `--staged` - Check only staged files (skip unstaged)
- `--no-tests` - Skip test discovery and execution
- `--all-tests` - Run the full test suite instead of only related tests

## Example Usage
```
/review-changes
/review-changes --fix
/review-changes --staged
/review-changes --no-tests
/review-changes --all-tests
```

## Auto-fix Mode (`--fix`)

When `--fix` is passed, run auto-fixers first, then re-check:
```bash
hatch run lint:fmt <changed_py_files>
```
`lint:fmt` runs `ruff format`, `ruff check --fix`, then re-runs `lint:style` to confirm clean.

## Related Test Discovery

By default, find and run tests related to changed files:

1. **Direct test files**: If `tests/foo/test_bar.py` changed, run it directly
2. **Source → Test mapping**: If `safety/scan/foo.py` changed, look for `tests/scan/test_foo.py`
3. **Model/constants changes**: If `safety/models/` or `safety/constants.py` changed, run all unit tests

```bash
# With active .venv
pytest <discovered_test_files> -m "unit or basic" -v

# Or via hatch (no .venv required)
hatch run test.py3.9:test -- <discovered_test_files> -m "unit or basic" -v
```

If no related tests are found for changed source files, note this in the output but don't fail.

**Note**: Test discovery is best-effort. When in doubt, run the full suite:
```bash
pytest tests/ -m "unit or basic"
```

## Output Format
```markdown
## Files Checked (N)
- safety/scan/foo.py
- tests/scan/test_foo.py

## Results
✓ Format: OK
✗ Lint: 2 issues
  - safety/scan/foo.py:45: F401 unused import 'os'
  - safety/scan/foo.py:87: E711 comparison to None
✓ Types: OK  (scoped to safety/scan/ per pyproject.toml)
✓ Tests: 3 passed

## Suggested Fixes
Run `/review-changes --fix` to auto-fix, or manually:
  hatch run lint:fmt safety/scan/foo.py
```

## Why This Exists

CI runs `hatch run lint:all ${FILES}` on every PR. This command replicates that check locally
so issues are caught before pushing. It is intentionally scoped to changed files only for speed.
