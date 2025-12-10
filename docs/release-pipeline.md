# Release Pipeline Documentation

This document describes the automated release pipeline for Secure Password Manager.

## Overview

The project uses GitHub Actions for continuous integration and automated releases. The pipeline includes:

1. **Automated Testing**: Run tests on multiple Python versions and platforms
2. **Code Quality**: Linting and type checking
3. **Security Scanning**: Vulnerability detection
4. **Build Verification**: Package building and validation
5. **Automated Releases**: Version management and PyPI publishing

## Workflow Files

### `.github/workflows/ci-cd.yml`

Main CI/CD pipeline that runs on:

- Push to `main` or `develop` branches
- Pull requests to `main`
- GitHub release events

**Jobs:**

- `test`: Run pytest on Python 3.8-3.12 across Ubuntu, macOS, Windows
- `lint`: Run ruff and mypy for code quality
- `security`: Run safety and bandit for security scanning
- `build`: Build distribution packages (sdist and wheel)
- `release`: Publish to PyPI and upload release assets (only on release events)

## Creating a Release

### Manual Release Process

1. **Update Version**

   ```bash
   # Bump patch version (e.g., 1.10.3 -> 1.10.4)
   python scripts/bump_version.py patch

   # Bump minor version (e.g., 1.10.3 -> 1.11.0)
   python scripts/bump_version.py minor

   # Bump major version (e.g., 1.10.3 -> 2.0.0)
   python scripts/bump_version.py major

   # Or set explicit version
   python scripts/bump_version.py patch --new-version 1.10.4
   ```

   This updates:
   - `VERSION.txt`
   - `src/secure_password_manager/__init__.py`
   - `pyproject.toml`
   - `browser-extension/manifest.json`
   - `browser-extension/manifest-firefox.json`
   - `CHANGELOG.md` (adds new entry template)

2. **Update CHANGELOG.md**

   Fill in the release notes in the newly created section:

   ```markdown
   ## [1.10.4] - 2025-12-09

   ### Added
   - Domain socket transport for browser bridge
   - Bulk operations for multi-select entries
   - pytest-qt smoke test suite

   ### Changed
   - Improved security audit performance with parallel processing

   ### Fixed
   - Fixed certificate fingerprint format in TLS module
   ```

3. **Commit and Push**

   ```bash
   git add -A
   git commit -m "Bump version to 1.10.4"
   git push origin main
   ```

4. **Create GitHub Release**

   ```bash
   # Create and push tag
   git tag -a v1.10.4 -m "Release v1.10.4"
   git push origin v1.10.4
   ```

   Or use the version bump script with `--tag --push`:

   ```bash
   python scripts/bump_version.py patch --tag --push
   ```

5. **Create GitHub Release via Web UI**

   - Go to <https://github.com/YOUR_USERNAME/Password_Manager/releases/new>
   - Select tag: `v1.10.4`
   - Title: `v1.10.4`
   - Description: Copy relevant section from CHANGELOG.md
   - Check "Set as latest release"
   - Click "Publish release"

   This triggers the `release` job which:
   - Builds distribution packages
   - Publishes to PyPI (requires `PYPI_API_TOKEN` secret)
   - Uploads release assets (sdist, wheel)

### Automated Release via GitHub Actions

Once you create a GitHub release, the pipeline automatically:

1. **Runs All Tests**: Ensures quality before publishing
2. **Builds Packages**: Creates source distribution and wheel
3. **Publishes to PyPI**: Uploads packages (requires API token)
4. **Attaches Assets**: Adds built packages to GitHub release

## Configuration

### Required Secrets

Add these secrets in GitHub repository settings (Settings → Secrets → Actions):

#### `PYPI_API_TOKEN`

Token for publishing to PyPI:

1. Go to <https://pypi.org/manage/account/token/>
2. Create new API token with scope for your project
3. Copy token (starts with `pypi-`)
4. Add as repository secret

### Optional Secrets

#### `CODECOV_TOKEN`

For code coverage reporting:

1. Sign up at <https://codecov.io>
2. Add your repository
3. Copy upload token
4. Add as repository secret

## Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **PATCH** (e.g., 1.10.3 → 1.10.4): Bug fixes, no new features
- **MINOR** (e.g., 1.10.3 → 1.11.0): New features, backward compatible
- **MAJOR** (e.g., 1.10.3 → 2.0.0): Breaking changes

## Testing Pipeline Locally

Before pushing, test the pipeline locally:

### Run Tests

```bash
pytest --cov=src/secure_password_manager --cov-report=term -v
```

### Run Linters

```bash
# Install tools
pip install ruff mypy

# Run checks
ruff check src/ tests/
mypy src/ --ignore-missing-imports
```

### Run Security Scans

```bash
# Install tools
pip install safety bandit

# Run scans
safety check
bandit -r src/ -ll
```

### Build Packages

```bash
# Install build tools
pip install build twine

# Build
python -m build

# Check
twine check dist/*
```

## Rollback Procedure

If a release has issues:

1. **Yank PyPI Release**

   ```bash
   pip install twine
   twine yank <package> <version>
   ```

   Or via PyPI web UI: Project → Releases → Yank release

2. **Delete GitHub Release**

   - Go to Releases page
   - Click release → Edit
   - Scroll down → Delete release

3. **Delete Git Tag**

   ```bash
   git tag -d v1.10.4
   git push origin :refs/tags/v1.10.4
   ```

4. **Revert Version**

   ```bash
   # Manually edit VERSION.txt and other files back to previous version
   # Or use bump_version.py with explicit version
   python scripts/bump_version.py patch --new-version 1.10.3

   git add -A
   git commit -m "Revert to v1.10.3"
   git push
   ```

## Pre-Release Checklist

Before creating a release:

- [ ] All tests passing locally
- [ ] CHANGELOG.md updated with release notes
- [ ] Documentation updated (if needed)
- [ ] Browser extensions tested
- [ ] Version numbers consistent across files
- [ ] No uncommitted changes
- [ ] CI passing on main branch

## Post-Release Checklist

After publishing:

- [ ] Verify PyPI release: <https://pypi.org/project/secure-password-manager/>
- [ ] Verify GitHub release has assets attached
- [ ] Test installation from PyPI: `pip install --upgrade secure-password-manager`
- [ ] Update documentation site (if applicable)
- [ ] Announce on social media/forums (if applicable)
- [ ] Monitor for user reports

## Troubleshooting

### CI Tests Fail

- Check test logs in GitHub Actions
- Run tests locally: `pytest -v`
- Fix issues, push fix, re-run workflow

### PyPI Upload Fails

Common issues:

- **Invalid token**: Regenerate PYPI_API_TOKEN secret
- **Version already exists**: PyPI doesn't allow re-uploading same version
  - Delete release and tag
  - Bump patch version
  - Re-release
- **Package validation fails**: Run `twine check dist/*` locally

### Build Artifacts Missing

- Check build job logs
- Ensure `build` job completed successfully
- Verify artifact upload step didn't fail

### Release Job Doesn't Trigger

- Verify release event type is `created` (not `published` or `edited`)
- Check workflow file syntax
- Ensure secrets are configured

## Continuous Delivery vs Continuous Deployment

Current setup: **Continuous Delivery**

- Code is automatically tested and built
- Release requires manual GitHub release creation
- Provides control over release timing

To enable **Continuous Deployment** (automatic releases):

- Add auto-tagging on version changes
- Trigger release job on tag push instead of GitHub release
- Requires high confidence in test coverage

## Maintenance

### Updating Workflow

When modifying `.github/workflows/ci-cd.yml`:

1. Test changes on a feature branch
2. Create PR to main
3. Verify workflow runs successfully
4. Merge after approval

### Python Version Updates

When adding/removing Python versions:

1. Update `matrix.python-version` in workflow
2. Update `pyproject.toml` classifiers
3. Update `README.md` requirements
4. Test locally with new versions

### Dependency Updates

Regularly update GitHub Actions:

```bash
# Check for action updates
# Visit https://github.com/actions/checkout/releases
# Update version in workflow file
```

Update Python dependencies:

```bash
pip install --upgrade pip setuptools wheel
pip list --outdated
```

## Monitoring

Track release pipeline health:

- **GitHub Actions**: Repository → Actions tab
- **PyPI Downloads**: <https://pypistats.org/packages/secure-password-manager>
- **Test Coverage**: Codecov dashboard
- **Security Advisories**: GitHub Security tab

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
