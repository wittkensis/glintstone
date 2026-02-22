# Git Hooks for Glintstone

Automated quality gates and validation checks for the Glintstone project.

## Overview

This directory contains custom git hooks that enforce code quality, documentation consistency, and database integrity. Hooks are managed by the [pre-commit framework](https://pre-commit.com).

## Installed Hooks

### Pre-Commit Hooks (Run Before Each Commit)

#### 1. **Python Code Quality** (`pre-commit.sh`)
- **What it does:** Runs `ruff` (linter + formatter) and `mypy` (type checker) on staged Python files
- **Prevents:** Syntax errors, import issues, type errors, formatting inconsistencies
- **Auto-fix:** Run `ruff format <file>` to fix formatting issues
- **Skip:** `git commit --no-verify` (not recommended)

#### 2. **Documentation Validation** (`pre-commit-docs.sh`)
- **What it does:** Ensures documentation is updated when code changes
- **Checks:**
  - Schema changes require README/docs update
  - New import scripts require README update
  - API route changes prompt README review
  - Warns about missing docstrings
- **Fix:** Update corresponding documentation before committing

#### 3. **Standard Checks** (from `pre-commit-hooks`)
- Trailing whitespace removal
- End-of-file fixer
- YAML validation
- Large file detection (>1MB)
- Merge conflict markers
- Mixed line endings

### Pre-Push Hooks (Run Before Push)

#### 4. **Database Schema Validation** (`pre-push.sh`)
- **What it does:** Validates schema YAML and checks for uncommitted migrations
- **Prevents:** Pushing invalid schema changes or forgetting migration files
- **Fix:** Ensure `data-model/glintstone-v2-schema.yaml` is valid YAML and commit all migrations

### Post-Merge Hooks (Run After Merge)

#### 5. **Dependency Sync Warnings** (`post-merge.sh`)
- **What it does:** Alerts when dependencies/config change after merge
- **Warnings:**
  - `requirements.txt` → run `pip install -r requirements.txt`
  - `.env.example` → review and update `.env`
  - `data-model/` → review migrations
  - `ops/local/` → restart dev servers

## Installation

Hooks are automatically installed via the pre-commit framework:

```bash
# Already done during Phase 1 implementation:
pip install pre-commit ruff mypy
pre-commit install
pre-commit install --hook-type pre-push
pre-commit install --hook-type post-merge
```

## Usage

### Running Hooks Manually

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run python-quality --all-files
pre-commit run documentation-validation --all-files

# Run hooks on specific files
pre-commit run --files source-data/import-tools/*.py
```

### Bypassing Hooks (Emergency Use Only)

```bash
# Skip all hooks (NOT RECOMMENDED)
git commit --no-verify

# Skip specific hook (edit .pre-commit-config.yaml temporarily)
```

### Updating Hooks

```bash
# Update to latest hook versions
pre-commit autoupdate

# Migrate deprecated config
pre-commit migrate-config
```

## Fixing Common Issues

### Issue: Ruff finds unused variables

**Error:** `F841 Local variable 'foo' is assigned to but never used`

**Fix options:**
1. Remove the unused variable
2. Prefix with underscore: `_foo` (indicates intentionally unused)
3. Add `# noqa: F841` comment to suppress warning

### Issue: Documentation check fails

**Error:** `Schema changed but no documentation updated`

**Fix:** Update `README.md` or add documentation in `data-model/` before committing

### Issue: Type checking fails

**Error:** `error: Missing type annotation for variable`

**Fix:** Add type hints:
```python
# Before
result = get_data()

# After
result: dict = get_data()
# or
result: dict[str, Any] = get_data()
```

### Issue: YAML validation fails

**Error:** `Schema YAML is invalid`

**Fix:** Validate YAML syntax:
```bash
python3 -c "import yaml; yaml.safe_load(open('data-model/glintstone-v2-schema.yaml'))"
```

## Configuration

### `.pre-commit-config.yaml`
Main configuration file defining which hooks run and when.

### Hook Scripts
- `ops/hooks/pre-commit.sh` - Python quality checks
- `ops/hooks/pre-commit-docs.sh` - Documentation validation
- `ops/hooks/pre-push.sh` - Schema validation
- `ops/hooks/post-merge.sh` - Dependency warnings

## Existing Code Issues

Initial run on existing codebase found:
- **8 unused variable warnings** in import scripts and ML code
- These are non-blocking (warnings only) but should be cleaned up

To fix:
```bash
# Review and fix unused variables
ruff check --select F841 .

# Auto-remove unused variables (review changes carefully)
ruff check --select F841 --fix .
```

## Testing

Verify hooks work correctly:

```bash
# 1. Test Python quality check
echo "import sys; def foo():" > test.py
git add test.py
git commit -m "test"  # Should fail (syntax error)
rm test.py

# 2. Test documentation check
echo "test: true" > data-model/test.yaml
git add data-model/test.yaml
git commit -m "test"  # Should fail (no docs updated)
rm data-model/test.yaml

# 3. Test pre-push validation
pre-commit run schema-validation --hook-stage push
```

## Performance

- **Pre-commit:** ~2-5 seconds on typical commit (few files)
- **All files:** ~30-60 seconds on entire codebase
- Hooks run in parallel where possible
- Environments cached after first run

## Troubleshooting

### Hooks not running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install --install-hooks
```

### Permission denied errors

```bash
# Make scripts executable
chmod +x ops/hooks/*.sh
```

### Pre-commit framework errors

```bash
# Clear cache and reinstall
pre-commit clean
pre-commit install-hooks
```

## Migration from Git LFS Hooks

The pre-commit framework runs in "migration mode" to preserve existing Git LFS hooks. Both sets of hooks run together - this is intentional and correct.

## Next Steps

See [Phase 2 plan](/.claude/plans/hidden-marinating-zephyr.md) for Claude Code hooks implementation.
