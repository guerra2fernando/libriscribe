from setuptools import find_packages, setup

setup(
    name="libriscribe",
    version="0.4.0",
    python_requires=">=3.10",
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
        "google-genai>=2.7.0",
        "rich",
        "pick",
    ],
    entry_points={
        "console_scripts": [
            "libriscribe=libriscribe.main:app",  # Updated entry point
        ],
    },
)
