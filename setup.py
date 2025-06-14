from setuptools import setup, find_packages

setup(
    name="libriscribe",
    version="0.3.0",
    packages=find_packages(),
    package_dir={"libriscribe": "src/libriscribe"},
    install_requires=[
        "typer",
        "openai",
        "python-dotenv",
        "pydantic",
        "pydantic-settings",
        "beautifulsoup4",
        "requests",
        "markdown",
        "fpdf",
        "tenacity",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
            "isort",
        ],
    },
    entry_points={
        "console_scripts": [
            "libriscribe=libriscribe.main:app",  # Updated entry point
        ],
    },
)
