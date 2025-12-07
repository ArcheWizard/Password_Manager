# Testing & Quality Guide

This guide defines how Secure Password Manager is verified. It covers test layers, tooling, metrics, and workflows for keeping quality high.

## Objectives

1. Maintain ≥90% line coverage on `src/secure_password_manager`.
2. Exercise critical workflows (auth, crypto, backup, audit, GUI) in automated tests.
3. Catch regressions early via continuous integration.
4. Document manual verification steps for releases.

## Test Inventory

| Layer | Location | Purpose | Status |
| --- | --- | --- | --- |
| Unit | `tests/test_*.py` | Validate functions in isolation (crypto, database, password analysis, key management, password history, clipboard, config). | ✅ Implemented |
| Integration | `tests/test_integration.py` | Exercise real database + crypto files in temp directories. | ✅ Implemented |
| Browser Bridge | `tests/test_browser_bridge.py` | Token store persistence, validation, and expiration. | ✅ Implemented |
| Approval System | `tests/test_approval_manager.py`, `tests/test_browser_bridge_approval.py` | Approval manager, store persistence, CLI/GUI prompt handlers, remembered decisions. | ✅ Implemented |
| Advanced Crypto | `tests/test_crypto_advanced.py` | KDF versioning, envelope encryption, HMAC verification. | ✅ Implemented |
| Security Audit | `tests/test_security_audit.py`, `tests/test_security_analyzer.py` | Password strength evaluation, breach checking, audit workflow. | ✅ Implemented |
| Two-Factor Auth | `tests/test_two_factor.py` | TOTP generation, QR codes, verification, configuration persistence. | ✅ Implemented |
| Property-based (planned) | `tests/property/test_crypto_props.py` | Randomized inputs for crypto and database operations. | ❌ Planned |
| GUI smoke (planned) | `tests/gui/test_main_window.py` | Use `pytest-qt` to ensure dialogs load, actions wire correctly. | ❌ Planned |
| Browser Extension (manual) | `browser-extension/` | Manual testing of pairing, auto-fill, credential saving across Chrome/Firefox. | 🔵 Manual |
| End-to-end scripts | `scripts/initialize.py --demo` + manual checks | Validate packaging, CLI/GUI parity. | 🔵 Partial |

## Tooling

- **Test runner**: `pytest`
- **Coverage**: `pytest-cov` with HTML report (`.coverage`, `htmlcov/`)
- **Linting**: `ruff`, `black`, `isort`, `mypy` (optional but encouraged)

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=secure_password_manager --cov-report=term --cov-report=html
```

GUI tests (planned):

```bash
pytest -m gui --qt-log-level=INFO
```

## Fixtures & Helpers

- `tests/conftest.py` defines:
  - `test_env`: temporary directory scaffolding.
  - `clean_crypto_files`: fresh key/salt/auth files per test.
  - `clean_database`: isolated SQLite file with schema initialization.
- Use `monkeypatch` for isolating environment variables and file paths.

## Coverage Expectations

| Component | Target |
| --- | --- |
| `utils/crypto.py` | 100% (critical security component) |
| `utils/database.py` | ≥95% including migrations and error paths |
| `utils/security_audit.py` | ≥90% (branch coverage for issue categories) |
| `apps/app.py` | ≥80% via CLI-driven tests and command harness |
| `apps/gui.py` | ≥70% via pytest-qt smoke tests and presenter unit tests |

Failing to meet thresholds should block CI until addressed.

## Regression Playbooks

1. **Bug Reproduction**: Write a failing test first.
2. **Fix Implementation**: Patch code with minimal scope.
3. **Guardrail**: Keep the new test to prevent regressions.
4. **Documentation**: Update relevant manuals if behavior changed.

## Manual Verification Checklist (Per Release)

1. Clean install on Linux/macOS/Windows.
2. Create vault, add multiple entries, verify CLI/GUI sync.
3. Run security audit; confirm weak/reused/expired detection.
4. Generate backup, delete local files, restore, verify integrity.
5. Enable 2FA, restart app, ensure prompt flows.
6. Trigger breach check (online/offline) and review logs.

## Continuous Integration (Planned)

- GitHub Actions matrix (`ubuntu-latest`, `macos-latest`, `windows-latest`).
- Steps: install deps, lint, run unit + integration tests, upload coverage & build artifacts.
- Required status checks before merging to `main`.

## Future Enhancements

- Fuzz tests for import/export parsers using `hypothesis`.
- Headless GUI regression suite covering drag/drop, bulk selection, and theme changes.
- Scenario tests for browser extension IPC once implemented.
