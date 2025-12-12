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
| Unit | `tests/test_*.py` | Validate functions in isolation (crypto, database, password analysis, key management, password history, clipboard, config, logger, paths, interactive, ui). | ✅ Implemented |
| Integration | `tests/test_integration.py` | Exercise real database + crypto files in temp directories. | ✅ Implemented |
| Browser Bridge | `tests/test_browser_bridge.py` | Token store persistence, validation, and expiration; credential storage endpoint. | ✅ Implemented |
| Approval System | `tests/test_approval_manager.py`, `tests/test_browser_bridge_approval.py` | Approval manager, store persistence, CLI/GUI prompt handlers, remembered decisions. | ✅ Implemented |
| Advanced Crypto | `tests/test_crypto_advanced.py` | KDF versioning, envelope encryption, HMAC verification. | ✅ Implemented |
| Security Audit | `tests/test_security_audit.py`, `tests/test_security_analyzer.py` | Password strength evaluation, breach checking, audit workflow. | ✅ Implemented |
| Two-Factor Auth | `tests/test_two_factor.py` | TOTP generation, QR codes, verification, configuration persistence. | ✅ Implemented |
| Backup & Restore | `tests/test_backup.py` | Export/import with encryption, full backup/restore, metadata preservation. | ✅ Implemented |
| Payload Encryption | `tests/test_payload_encryption.py` | End-to-end payload encryption for browser bridge, AES-GCM with HKDF. | ✅ Implemented |
| Path Management | `tests/test_paths.py` | XDG directory resolution, development vs production mode, path helpers. | ✅ Implemented |
| Logging | `tests/test_logger.py` | Log file creation, log entry retrieval, log clearing with backup. | ✅ Implemented |
| Interactive CLI | `tests/test_interactive.py` | Menu selection, confirmation prompts, hidden input. | ✅ Implemented |
| UI Formatting | `tests/test_ui.py` | Console output formatting, headers, tables, colored messages. | ✅ Implemented |
| GUI Smoke | `tests/test_gui_smoke.py` | PyQt5 GUI smoke tests for critical workflows. | ✅ Implemented |
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
pytest --cov=src/secure_password_manager --cov-report=term --cov-report=html
```

With coverage enforcement (≥90% required):

```bash
pytest --cov=src/secure_password_manager --cov-report=term --cov-report=html --cov-fail-under=90
```

GUI tests:

```bash
pytest tests/test_gui_smoke.py --qt-log-level=INFO
```

Run specific test modules:

```bash
pytest tests/test_backup.py -v
pytest tests/test_payload_encryption.py -v
pytest tests/test_paths.py -v
```

## Test Isolation & Safety

**Critical**: All tests **must** be completely isolated from production data to prevent accidental data loss or corruption.

### Isolation Architecture

The test suite implements comprehensive isolation through:

1. **Path Monkeypatching**: All `get_*_path()` functions redirected to temporary directories
2. **Module State Reset**: Crypto context and logger state cleared between tests
3. **Wildcard Cleanup**: Glob patterns (`secret.key*`) catch all generated files including backups
4. **Session Safeguard**: Warning system for production directory access attempts

### Fixtures & Helpers

`tests/conftest.py` provides the following isolation fixtures:

#### `test_env` (Base Fixture)

Creates isolated temporary directory structure:

- `test_data/` - database, keys, auth files
- `test_config/` - settings, certificates
- `test_cache/` - breach cache, temp files
- `test_logs/` - log files
- `test_data/backups/` - backup storage

Monkeypatches all path functions:

```python
get_data_dir() → /tmp/pytest-xxx/test_data/
get_database_path() → /tmp/pytest-xxx/test_data/passwords.db
get_secret_key_path() → /tmp/pytest-xxx/test_data/secret.key
# ... and 10+ other path functions
```

#### `clean_crypto_files` (Crypto Isolation)

Removes all crypto files before and after each test:

- `secret.key*` (includes `.bak` timestamped backups)
- `crypto.salt*`
- `auth.json*`

Resets `crypto._MASTER_PW_CONTEXT = None`

#### `clean_database` (Database Isolation)

Initializes fresh database with:

- Connection cleanup before deletion
- Schema migration to latest version
- Proper cleanup in teardown

#### `isolated_environment` (Complete Isolation)

**Recommended for all new tests**. Combines all isolation fixtures:

```python
def test_something(isolated_environment):
    # Guaranteed fresh state with no production access
    generate_key()  # ✅ Goes to /tmp/
    init_db()       # ✅ Goes to /tmp/
    # All .bak files created in /tmp/ only
```

### Usage Guidelines

**✅ DO:**

```python
# Use isolated_environment for complete isolation
def test_feature(isolated_environment):
    generate_key()
    init_db()
    # Safe - all operations in temp directory

# Or combine individual fixtures explicitly
def test_crypto_only(test_env, clean_crypto_files):
    generate_key()
    # Safe - crypto operations isolated
```

**❌ DON'T:**

```python
# Never use test_env alone - incomplete isolation!
def test_bad(test_env):
    generate_key()  # ⚠️ May not be fully isolated

# Never import paths module at test file top level
from secure_password_manager.utils.paths import get_data_dir
data = get_data_dir()  # ❌ Called before fixtures run!
```

### Verification

Run isolation tests to verify protection:

```bash
pytest tests/test_isolation.py -v
```

These tests verify:

- ✅ All paths point to `/tmp/` or temp directories
- ✅ `.bak` files created only in temp directories
- ✅ Production `.data/` directory never modified
- ✅ Each test starts with clean environment
- ✅ All cleanup patterns work correctly

### Production Data Protection

Multiple layers protect your production data:

1. **Monkeypatch**: Path functions return temp directories
2. **Cleanup**: Wildcard patterns remove all generated files
3. **Isolation Verification**: `tests/test_isolation.py` validates protection
4. **CI Enforcement**: Tests run on all platforms to catch leaks

**Before running tests**, ensure you're using the fixtures correctly. If in doubt, use `isolated_environment`.

## Coverage Expectations

**Overall Target: ≥90% line coverage on `src/secure_password_manager`**

| Component | Target | Notes |
| --- | --- | --- |
| `utils/crypto.py` | ≥92% | Critical security component with comprehensive edge case testing |
| `utils/database.py` | ≥89% | Includes migrations and error paths |
| `utils/security_audit.py` | ≥85% | Branch coverage for issue categories |
| `utils/backup.py` | ≥90% | Full backup/restore with encryption and metadata |
| `utils/payload_encryption.py` | ≥90% | End-to-end payload encryption for browser bridge |
| `utils/paths.py` | ≥90% | XDG directory resolution and development mode detection |
| `utils/logger.py` | ≥85% | Logging infrastructure with error handling |
| `utils/clipboard_manager.py` | 100% | Auto-clear functionality fully tested |
| `utils/config.py` | 100% | Configuration management |
| `utils/password_analysis.py` | 100% | Password strength evaluation |
| `utils/security_analyzer.py` | ≥98% | Breach checking and analysis |
| `utils/two_factor.py` | 100% | TOTP authentication |
| `utils/tls.py` | ≥96% | TLS certificate generation |
| `utils/approval_manager.py` | ≥90% | Browser bridge approval system |
| `utils/interactive.py` | ≥80% | CLI interaction helpers |
| `utils/ui.py` | ≥80% | Console formatting utilities |
| `services/browser_bridge.py` | ≥85% | FastAPI endpoints and token management |
| `apps/gui.py` | ≥70% | PyQt5 GUI via smoke tests |
| `apps/app.py` | Target: 40-50% | CLI application (hybrid approach: core functions tested, full menu flows manual) |

### Coverage Enforcement

- **CI/CD**: Tests fail if overall coverage drops below 90%
- **Branch Protection**: GitHub branch protection requires passing tests
- **Codecov Integration**: Automatic coverage reporting and tracking
- **Local Validation**: Run `pytest --cov-fail-under=90` before committing

### Coverage Configuration

Coverage settings are defined in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src/secure_password_manager"]
omit = ["*/tests/*", "*/test_*.py", "*/__pycache__/*", "*/conftest.py"]
branch = true

[tool.coverage.report]
fail_under = 90
show_missing = true
precision = 2
```

Codecov thresholds in `codecov.yml`:

```yaml
coverage:
  status:
    project:
      default:
        target: 90%
        threshold: 1%
    patch:
      default:
        target: 85%
        threshold: 2%
```

Failing to meet thresholds blocks CI and prevents merging to protected branches.

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

## Continuous Integration

-**Status: ✅ Implemented**

GitHub Actions matrix runs tests on:

- **OS**: `ubuntu-latest`, `macos-latest`, `windows-latest`
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12

### CI Pipeline Jobs

1. **test**: Run full test suite with coverage
   - Install dependencies
   - Execute `pytest --cov --cov-fail-under=90`
   - Upload coverage to Codecov (Ubuntu + Python 3.11 only)

2. **lint**: Code quality checks
   - Run `ruff check src/ tests/`
   - Run `mypy src/` for type checking

3. **security**: Security scanning
   - Run `safety check` for dependency vulnerabilities
   - Run `bandit -r src/` for code security issues

4. **build**: Package building
   - Build source and wheel distributions
   - Verify packages with `twine check`

### Branch Protection Rules

Recommended GitHub branch protection settings for `main`:

- ✅ Require status checks to pass before merging
  - Required checks: `test`, `lint`
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Include administrators in restrictions

### Coverage Reporting

- **Codecov** uploads coverage from Ubuntu + Python 3.11 runs
- **fail_ci_if_error: true** ensures coverage upload failures block CI
- Pull requests show coverage diff in comments
- Project/patch coverage thresholds enforced automatically

## Future Enhancements

- Fuzz tests for import/export parsers using `hypothesis`.
- Headless GUI regression suite covering drag/drop, bulk selection, and theme changes.
- Scenario tests for browser extension IPC once implemented.
