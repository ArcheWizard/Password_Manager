# Contribution Guide

Thank you for helping improve Secure Password Manager. This guide explains how to propose changes, follow coding standards, and verify your work.

## Code of Conduct

Contributors are expected to treat others with respect, offer constructive feedback, and keep security disclosures responsible. Report unacceptable behavior through the project’s issue tracker or contact channel listed in `README.md`.

## Development Environment

1. Fork and clone the repository.
2. Create a virtual environment (`python3 -m venv .venv`).
3. Install dependencies (`pip install -e .[dev]` when extras become available).
4. Activate pre-commit hooks (planned) to enforce formatting.

### Development vs Production Mode

The application automatically detects whether it's running in development or production mode:

**Development Mode** (recommended for contributors):

- Install with: `pip install -e .`
- Data stored in: `.data/` directory in project root
- Code changes take effect immediately (no reinstall needed)
- Activated when:
  - Code is NOT in `site-packages` or `dist-packages`
  - `.data/` directory exists in project root
  - `src/` or `pyproject.toml` exists (confirms source tree)

**Production Mode**:

- Install with: `pip install secure-password-manager`
- Data stored in: XDG directories (`~/.local/share`, `~/.config`, `~/.cache`)
- Code changes require reinstall
- Activated when:
  - Code is in `site-packages` or `dist-packages` (pip-installed)

**Quick Mode Check**:

```bash
python -c "from secure_password_manager.utils.paths import is_development_mode; print(f'Development mode: {is_development_mode()}')"
```

**Switching Modes**:

```bash
# To development mode
pip uninstall secure-password-manager
pip install -e .
mkdir -p .data

# To production mode
pip uninstall secure-password-manager
pip install secure-password-manager
```

## Branching & Workflow

1. Create a descriptive branch name: `feature/browser-ipc`, `fix/audit-deadlock`.
2. Keep pull requests focused on a single problem.
3. Rebase on `main` before submitting to minimize merge conflicts.
4. Reference related issues in commit messages and PR descriptions.

## Coding Standards

- Follow Python 3.8+ syntax where feasible while keeping compatibility with the minimum supported version (3.8).
- Run `ruff`, `black`, and `isort` on touched files.
- Prefer dependency injection for services (database, crypto) to simplify testing.
- Keep UI layers thin; add shared logic to `utils/` modules.
- Default to ASCII unless Unicode is required.

## Testing Requirements

**Critical**: All tests must use proper isolation fixtures to prevent production data modification.

### Test Isolation

**Always use the `isolated_environment` fixture** for new tests:

```python
def test_my_feature(isolated_environment):
    # Guaranteed fresh state, no production access
    generate_key()  # ✅ Isolated to /tmp/
    init_db()       # ✅ Isolated to /tmp/
    # All operations safe
```

**Available fixtures** (from `tests/conftest.py`):

- `isolated_environment` - **Recommended**: Complete isolation (combines all fixtures below)
- `test_env` - Base fixture with path monkeypatching
- `clean_crypto_files` - Removes all crypto files (including `.bak` backups)
- `clean_database` - Fresh database with schema

**Never:**

- Use `test_env` alone without `clean_crypto_files` and `clean_database`
- Import path functions at module level (breaks monkeypatching)
- Write files directly to `.data/` in tests

See `docs/testing-quality.md` for complete isolation documentation.

### Running Tests

- `pytest --cov=secure_password_manager` must pass locally.
- Add regression tests for every bug fix.
- GUI-related changes should accompany pytest-qt smoke tests or manual verification steps listed in the PR description.
- Document any new fixtures or helpers in `docs/testing-quality.md`.
- Run `pytest tests/test_isolation.py -v` to verify isolation is working.

## Documentation Expectations

- Update relevant guides when behavior or workflows change.
- Use concise, action-oriented language.
- Run markdown linting (`markdownlint-cli` or editor integration) before submitting.

## Commit Message Style

```text
<type>(scope): concise summary

body explaining motivation, context, testing
```

Examples:

- `feat(backup): add manifest integrity verification`
- `fix(gui): prevent clipboard leaks when window loses focus`

## Security Contributions

- Never include real secrets in tests, fixtures, or documentation.
- Coordinate vulnerability disclosures privately before opening public issues.
- Include threat-model updates in `docs/security-whitepaper.md` when introducing new surfaces.

## Release Participation

- Follow the checklist in `docs/build-release-handbook.md`.
- Double-check version bumps occur in `VERSION.txt`, `pyproject.toml`, and release notes.
- Tag releases as `vX.Y.Z` and attach signed artifacts.

## Getting Help

- Open a draft pull request for early feedback.
- Use Discussions/Issues for architectural proposals.
- Ping maintainers in the PR if reviews are blocked on domain-specific knowledge.
