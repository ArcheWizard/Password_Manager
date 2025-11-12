# Development

This guide covers local setup, running, testing, packaging, and release tips for Secure Password Manager.

## Prerequisites

- Python 3.8+
- OS dependencies for PyQt5 (Linux packages as needed)

## Getting Started

```bash
# Clone
git clone https://github.com/ArcheWizard/password-manager.git
cd password-manager

# Create and activate virtual env
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Editable install (optional)
pip install -e .
```

## Running

CLI:

```bash
password-manager
```

GUI:

```bash
password-manager-gui
```

Alternatively (from source):

```bash
python -m apps.app
python -m apps.gui
```

## Project Layout

- Entrypoints defined in `pyproject.toml` / `setup.py` under `[project.scripts]`
- Core modules in `utils/`
- Tests in `tests/`

## Testing

```bash
pytest -q
```

Notes:

- The integration test uses tempfile DBs and patches `DB_FILE`
- Network-dependent breach checks are limited and resilient to failures
- SQLite can lock under parallel operations; tests include small delays/workarounds

## Linting & Formatting (suggested)

This repository does not yet include linters/formatters configuration. Suggested tools:

- Ruff or Flake8 for linting
- Black for formatting
- isort for imports

Example setup (optional):

```bash
pip install ruff black isort
ruff check .
black .
isort .
```

## Packaging / Release

- Version is sourced from `VERSION.txt` (currently v1.7.0)
- Packaging is via `setuptools` with `pyproject.toml`
- To build:

```bash
python -m build
```

- To publish (example):

```bash
python -m twine upload dist/*
```

## Security and Secrets in Dev

- The app will generate `secret.key`, `crypto.salt`, `auth.json`, `totp_config.json` in the working directory
- Protect these files and avoid committing them
- Use separate test directories or temp files for experiments

## Troubleshooting

- Missing display libs for PyQt5: install system packages (e.g., `qt5-default`, `libxcb`) depending on distro
- Clipboard issues: ensure `pyperclip` has a backend (e.g., `xclip`/`xsel` on Linux)
- SQLite locked: close connections and avoid concurrent writes; add small delays if needed in tests
