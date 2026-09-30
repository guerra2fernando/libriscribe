from setuptools import find_packages, setup

setup(
    name="libriscribe",
    version="0.5.0",
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
        "boto3",
        "rich",
        "pick",
        "mcp>=1.9,<2",
    ],
    package_data={"libriscribe.prompt_templates": ["*.yml"]},
    extras_require={"semantic": ["sentence-transformers>=3.0,<6"]},
    entry_points={
        "console_scripts": [
            "libriscribe=libriscribe.main:app",  # Updated entry point
            "libriscribe-mcp=libriscribe.mcp_server:main",
        ],
    },
)
