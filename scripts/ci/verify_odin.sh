#!/usr/bin/env bash
set -euo pipefail

ODIN_TAG='dev-2026-08'
ODIN_ARCHIVE='odin-linux-amd64-dev-2026-08.tar.gz'
ODIN_SHA256='d858c0a182bb28d7b04b04dbb8aed592a9c96c84e4400ee917c74b45848a4d87'
ODIN_URL="https://github.com/odin-lang/Odin/releases/download/${ODIN_TAG}/${ODIN_ARCHIVE}"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
curl -fsSL --retry 3 --retry-delay 2 "$ODIN_URL" -o "$work/$ODIN_ARCHIVE"
echo "$ODIN_SHA256  $work/$ODIN_ARCHIVE" | sha256sum -c -
tar -xzf "$work/$ODIN_ARCHIVE" -C "$work"
ODIN_BIN="$(find "$work" -maxdepth 4 -type f -name odin | head -n 1)"
test -n "$ODIN_BIN"
chmod +x "$ODIN_BIN"
compiler_version="$($ODIN_BIN version)"

$ODIN_BIN check src/thermal_mesh.odin -file
$ODIN_BIN build src/thermal_mesh.odin -file -out:"$work/thermal_mesh"
program_output="$($work/thermal_mesh)"
printf '%s\n' "$program_output"
grep -F 'LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY' <<<"$program_output"
grep -F 'no control authority' <<<"$program_output"

mkdir -p .verification-artifacts
source_sha="$(sha256sum src/thermal_mesh.odin | awk '{print $1}')"
binary_sha="$(sha256sum "$work/thermal_mesh" | awk '{print $1}')"
export ODIN_TAG ODIN_ARCHIVE ODIN_SHA256 compiler_version source_sha binary_sha
python - <<'PY'
import json, os
from pathlib import Path
payload = {
    'schema': 'glaciereq.native-odin-thermal-proof.v1',
    'compiler_release': os.environ['ODIN_TAG'],
    'compiler_archive': os.environ['ODIN_ARCHIVE'],
    'compiler_archive_sha256': os.environ['ODIN_SHA256'],
    'compiler_version': os.environ['compiler_version'],
    'source_path': 'src/thermal_mesh.odin',
    'source_sha256': os.environ['source_sha'],
    'binary_sha256': os.environ['binary_sha'],
    'compile': 'PASS',
    'execute': 'PASS',
    'evidence_state': 'LOCAL_THERMAL_SCENARIO_MODEL_NOT_FLIGHT_TPS_AUTHORITY',
    'control_authority': False,
}
Path('.verification-artifacts/native-odin-thermal.json').write_text(
    json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8'
)
print(json.dumps(payload, sort_keys=True))
PY
