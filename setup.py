from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent

setup(
    name="libriscribe",
    version="0.5.1",
    description="A local-first, multi-agent writing assistant with project knowledge tools",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/guerra2fernando/libriscribe",
    project_urls={
        "Documentation": "https://guerra2fernando.github.io/libriscribe/",
        "Source": "https://github.com/guerra2fernando/libriscribe",
        "Issues": "https://github.com/guerra2fernando/libriscribe/issues",
        "Changelog": "https://github.com/guerra2fernando/libriscribe/blob/main/CHANGELOG.md",
    },
    license="MIT",
    license_files=("LICENSE",),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "typer",
        "python-dotenv",
        "pydantic",
        "pydantic-settings",
        "pyyaml",
        "beautifulsoup4",
        "requests",
        "markdown",
        "fpdf",
        "tenacity",
        "rich",
        "pick",
        "mcp>=1.9,<2",
    ],
    package_data={"libriscribe.prompt_templates": ["*.yml"]},
    extras_require={
        "openai": ["openai"],
        "anthropic": ["anthropic"],
        "google": ["google-genai>=2.7.0"],
        "bedrock": ["boto3"],
        "all-providers": ["openai", "anthropic", "google-genai>=2.7.0", "boto3"],
        "semantic": ["sentence-transformers>=3.0,<6"],
    },
    entry_points={
        "console_scripts": [
            "libriscribe=libriscribe.main:app",  # Updated entry point
            "libriscribe-mcp=libriscribe.mcp_server:main",
        ],
    },
)
