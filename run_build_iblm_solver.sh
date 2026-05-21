#!/usr/bin/env bash
set -euo pipefail

if ! command -v wmake >/dev/null 2>&1; then
  echo "wmake 未找到，请先 source OpenFOAM 环境。"
  exit 1
fi

wmake applications/solvers/coinIBLMSolver
