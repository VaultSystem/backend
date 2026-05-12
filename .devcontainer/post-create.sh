#!/usr/bin/env bash
set -euo pipefail

if [[ -f "uv.lock" ]]; then
  uv sync --frozen
else
  uv sync
fi

if [[ -f ".pre-commit-config.yaml" ]]; then
  uv run pre-commit install --install-hooks
fi
