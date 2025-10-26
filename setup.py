from setuptools import find_packages, setup

# Handle errors gracefully for missing files
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A secure local password manager application"

try:
    with open("VERSION.txt", "r") as f:
        version = f.read().strip()
except FileNotFoundError:
    version = "0.0.0"  # Fallback version

try:
    with open("requirements.txt", "r") as f:
        requirements = [
            line.strip() for line in f.readlines() if not line.startswith("#")
        ]
except FileNotFoundError:
    # Core dependencies with versions that work with Python 3.13
    requirements = [
        "cryptography>=41.0.0",
        "PyQt5>=5.15.9",
        "pillow>=10.0.0",  # Updated for Python 3.13 compatibility
        "zxcvbn>=4.4.28",
        "pytest>=7.0.0",
    ]

setup(
    name="secure-password-manager",
    version=version,
    author="ArcheWizard",
    author_email="your-email@example.com",
    description="A secure local password manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ArcheWizard/password-manager",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
    license="MIT",
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "password-manager=apps.app:main",
            "password-manager-gui=apps.gui:main",
        ],
    },
    include_package_data=True,
)
