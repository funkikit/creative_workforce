#!/usr/bin/env bash
set -euo pipefail

uv sync --directory backend
pnpm install --dir frontend
