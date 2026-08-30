# LibriScribe development instructions

## Environment setup

Use Python 3.10 or newer:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

The documentation site uses Node.js 18 or newer:

```bash
cd docs
npm ci
```

## Validation

Run the Python test suite:

```bash
pytest -q
```

Verify the package can be imported:

```bash
PYTHONPATH=src python -c "import libriscribe.main"
```

Build the documentation site when changing files under `docs/`:

```bash
cd docs
npm run build
```

## Project conventions

- Keep provider credentials in environment variables; never commit `.env` or API keys.
- Prefer focused changes and preserve existing CLI behavior.
- Add or update tests for behavioral changes.
- Do not make live LLM calls in tests unless explicitly requested.
- Report the validation commands run and any limitations in the final summary.
