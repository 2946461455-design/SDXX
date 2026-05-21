#!/usr/bin/env bash
set -euo pipefail

CASE_DIR="01_openfoam_case_iblm"

if ! command -v blockMesh >/dev/null 2>&1; then
  echo "OpenFOAM 命令不可用，请先 source OpenFOAM 环境。"
  exit 1
fi

blockMesh -case "$CASE_DIR"
coinIBLMSolver -case "$CASE_DIR"
