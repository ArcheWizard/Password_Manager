# Build & Release Handbook

Authoritative instructions for producing, verifying, and shipping Secure Password Manager releases.

## Release Cadence

- Target: quarterly feature releases, monthly maintenance updates as needed.
- Versioning: semantic (`MAJOR.MINOR.PATCH`).
- Current version: 1.8.4
- Source of truth: `VERSION.txt` (mirrored in `pyproject.toml` and `__init__.py`).

## Pre-Release Checklist

1. All issues for the milestone are closed or moved.
2. Tests pass with coverage ≥90%.
3. Documentation updated (README, user manual, security notes, roadmap).
4. Translations and accessibility items reviewed (if applicable).
5. Security review complete for new cryptography or IPC changes.

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip build twine pyinstaller
```

Requires Python 3.8 or newer. Verify with `python --version`.

## Building Python Packages

```bash
python -m build
```

Artifacts:

- `dist/password_manager-<version>.tar.gz`
- `dist/password_manager-<version>-py3-none-any.whl`

## Publishing to PyPI (Example)

1. Create an API token with upload access.
2. Run:

   ```bash
   python -m twine upload dist/*
   ```

3. Verify files on PyPI and tag release in Git.

## Desktop Bundles

### PyInstaller

```bash
pyinstaller scripts/password-manager.spec
pyinstaller scripts/password-manager-gui.spec
```

- Outputs go to `dist/` with per-platform folders.
- Ensure icons/resources under `assets/` are included.

### AppImage / Deb / App Bundle

Use the helper scripts under `scripts/`:

- `scripts/build_appimage.sh`
- `scripts/build_deb.sh`
- `scripts/build_linux_app.sh`

Each script writes artifacts to `releases/` with timestamped folders.

## Signing & Integrity

1. Generate SHA-256 checksums for every artifact:

   ```bash
   shasum -a 256 <file>
   ```

2. Sign archives using GPG:

   ```bash
   gpg --armor --detach-sign <file>
   ```

3. Publish signatures alongside downloads.

## Release Notes

- Update `CHANGELOG.md` with a new section.
- Summarize features, fixes, security improvements, and known issues.
- Include upgrade guidance (migrations, manual steps).

## Git Tagging

```bash
git tag -s vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

## Post-Release

1. Monitor issues for regressions.
2. Update roadmap to reflect completed work.
3. Archive logs and build outputs per compliance requirements.

## Hotfix Protocol

- Branch from the latest tag (`git checkout -b hotfix/vX.Y.Z+1 vX.Y.Z`).
- Apply fix, bump patch version, run tests.
- Release following the same checklist, noting the hotfix scope.

## Automation Opportunities

- GitHub Actions workflow that builds wheels, PyInstaller bundles, and AppImages per commit to `main`.
- Automatic draft release notes generated from merged PRs.
- Supply chain security: SBOM via `pip-audit` or `cyclonedx-bom`.
