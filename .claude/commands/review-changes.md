# Review Changes Command

Run quality checks on only the files that have changed (staged + unstaged), mirroring the CI lint job.

## Workflow

1. **Identify changed Python files**:
   ```bash
   # Unstaged + staged changes vs HEAD
   git diff --name-only HEAD
   git diff --name-only --cached
   ```
   Filter to `.py` files that still exist on disk. Deduplicate.

2. **Run targeted checks** (on changed files only):
   ```bash
   # Runs ruff check + ruff format --check --diff + pyright on the files
   hatch run lint:all <changed_py_files>
   ```
   This matches what CI does: `hatch run lint:all ${FILES}`.

   Note: `pyright` is configured in `[tool.pyright]` to include only `safety/scan/`. Files
   outside that path are still passed to pyright but will only be type-checked if pyright
   decides to process them. This matches CI behavior exactly.

3. **Report results**:
   - List files checked
   - Show any issues found
   - Suggest fixes (but do NOT auto-fix unless `--fix` is passed)

## Arguments

`$ARGUMENTS` - Optional flags:
- `--fix` - Auto-fix formatting and lint issues before checking
- `--staged` - Check only staged files (skip unstaged)
- `--with-tests` - Also discover and run related unit tests

## Example Usage

```
/review-changes
/review-changes --fix
/review-changes --staged
/review-changes --with-tests
```

## Auto-fix Mode (`--fix`)

When `--fix` is passed, run auto-fixers first, then re-check:

```bash
hatch run lint:fmt <changed_py_files>
```

`lint:fmt` runs `ruff format`, `ruff check --fix`, then re-runs `lint:style` to confirm clean.

## Related Test Discovery (`--with-tests`)

When `--with-tests` is specified, find and run tests related to changed files:

1. **Direct test files**: If `tests/foo/test_bar.py` changed, run it directly
2. **Source → Test mapping**: If `safety/scan/foo.py` changed, look for `tests/scan/test_foo.py`
3. **Model/constants changes**: If `safety/models/` or `safety/constants.py` changed, run all unit tests

```bash
# Example: discover related tests
for f in <changed_py_files>; do
  if [[ "$f" == tests/* ]]; then
    echo "$f"                                          # test file itself
  elif [[ "$f" == safety/models/* || "$f" == safety/constants.py ]]; then
    echo "tests/"                                      # broad impact — run all
    break
  else
    base=$(basename "$f" .py)
    find tests/ -name "test_${base}.py" 2>/dev/null   # matching test file
  fi
done | sort -u
```

Then run discovered tests with:
```bash
# With active .venv
pytest <discovered_test_files> -m "unit or basic" -v

# Or via hatch (no .venv required)
hatch run test.py3.9:test -- <discovered_test_files> -m "unit or basic" -v
```

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

## Suggested Fixes
Run `/review-changes --fix` to auto-fix, or manually:
  hatch run lint:fmt safety/scan/foo.py
```

## Why This Exists

CI runs `hatch run lint:all ${FILES}` on every PR. This command replicates that check locally
so issues are caught before pushing. It is intentionally scoped to changed files only for speed.
