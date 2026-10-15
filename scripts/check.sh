#!/usr/bin/env bash
# The one check. Runs every check this repository has, prints the counts, and
# exits non-zero on any failure. CI runs this file too, so no check exists only
# in CI.
#
#   unittest   every test under tests/ (the suite is standard library only)
set -uo pipefail
cd "$(dirname "$0")/.."

if [ -x .venv/bin/python ]; then py=.venv/bin/python; else py=python3; fi
command -v "$py" >/dev/null 2>&1 || { echo "check: $py is missing. Python 3.10 or newer is required." >&2; exit 2; }

log=$(mktemp)
trap 'rm -f "$log"' EXIT

echo "== unittest"
PYTHONPATH=src "$py" -m unittest discover -s tests -v 2>&1 | tee "$log"
rc=${PIPESTATUS[0]}

ran=$(grep -oE '^Ran [0-9]+' "$log" | tail -1 | grep -oE '[0-9]+' || echo 0)
failed=$(grep -oE '(failures|errors)=[0-9]+' "$log" | grep -oE '[0-9]+' | awk '{s+=$1} END {print s+0}')
failed=${failed:-0}
passed=$((ran - failed))

echo
echo "Checked $(date -u +%Y-%m-%d): unittest $passed passed, $failed failed."
if [ "$rc" -eq 0 ] && [ "$failed" -eq 0 ] && [ "$ran" -gt 0 ]; then
  echo "check: passed"
else
  echo "check: FAILED" >&2
  exit 1
fi
