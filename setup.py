from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("VERSION.txt", "r") as f:
    version = f.read().strip()

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f.readlines() if not line.startswith('#')]

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
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "password-manager=app:main",
            "password-manager-gui=gui:main",
        ],
    },
    include_package_data=True,
)