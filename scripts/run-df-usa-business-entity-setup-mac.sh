#!/bin/bash
# K16-Mutex Wrapper [CRUX-MK]
set -euo pipefail
LOCK_DIR="/tmp/df-usa-business-entity-setup.lock"
LOCK_AGE_LIMIT_S=21600
if [ -d "$LOCK_DIR" ]; then
    LOCK_AGE_S=$(( $(date +%s) - $(stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0) ))
    [ "$LOCK_AGE_S" -gt "$LOCK_AGE_LIMIT_S" ] && rm -rf "$LOCK_DIR"
fi
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "[K16-VETO] Lock held"; exit 3
fi
echo "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM
DF_DIR="/Users/make/Projects/dark-factories/df-usa-business-entity-setup"
cd "$DF_DIR"
export DF_USA_LLC_REAL_ENABLED="${DF_USA_LLC_REAL_ENABLED:-false}"
export PHRONESIS_TICKET="${PHRONESIS_TICKET:-MISSING}"
python3 -m src.adapter_orchestrator
