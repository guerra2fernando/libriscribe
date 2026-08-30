#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .

if [[ -f docs/package-lock.json ]]; then
  npm --prefix docs ci
fi
