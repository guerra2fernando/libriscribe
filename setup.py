from setuptools import find_packages, setup

setup(
    name="libriscribe",
    version="0.3.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "typer",
        "openai",
        "python-dotenv",
        "pydantic",
        "pydantic-settings",
        "pyyaml",
        "beautifulsoup4",
        "requests",
        "markdown",
        "fpdf",
        "tenacity",
        "anthropic",
        "google-generativeai",
        "rich",
        "pick",
    ],
    entry_points={
        "console_scripts": [
            "libriscribe=libriscribe.main:app",  # Updated entry point
        ],
    },
)
