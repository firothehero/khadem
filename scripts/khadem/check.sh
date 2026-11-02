#!/usr/bin/env bash
# Khadem post-sync gate for the agent: the Khadem contract tests + upstream i18n/prompt tests +
# the Arabic coverage report. Run after every upstream merge (sync-upstream.sh calls it).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
PY="${PYTHON:-python}"
"$PY" -m pytest -q -p no:cacheprovider -p no:xdist \
  tests/plugins/test_khadem_plugin.py \
  tests/agent/test_i18n.py tests/agent/test_i18n_layers.py tests/agent/test_system_prompt.py
"$PY" scripts/khadem/i18n_report.py
echo "✓ Khadem checks passed"
