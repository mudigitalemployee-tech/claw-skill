#!/usr/bin/env bash
# ============================================================================
# csv-dq-checker: Environment setup script
# Checks for Python3, pip, pandas, numpy — installs what's missing.
# Returns exit code 0 if Python path is ready, 1 if Python is unavailable.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[setup]${NC} $*"; }
warn() { echo -e "${YELLOW}[setup]${NC} $*"; }
err()  { echo -e "${RED}[setup]${NC} $*"; }

# --- 1. Find Python3 ---
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    err "Python 3.8+ not found."
    err "Attempting to install Python3..."

    # Try common package managers
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip 2>/dev/null && PYTHON="python3"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip 2>/dev/null && PYTHON="python3"
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3 python3-pip 2>/dev/null && PYTHON="python3"
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python python-pip 2>/dev/null && PYTHON="python3"
    elif command -v brew &>/dev/null; then
        brew install python3 2>/dev/null && PYTHON="python3"
    fi

    if [ -z "$PYTHON" ]; then
        err "Could not install Python3. Shell fallback will be used."
        exit 1
    fi
fi

log "Using Python: $($PYTHON --version 2>&1)"

# --- 2. Check/install pandas and numpy ---
install_pkg() {
    local pkg="$1"
    if ! $PYTHON -c "import $pkg" 2>/dev/null; then
        warn "$pkg not found. Installing..."
        if $PYTHON -m pip install "$pkg" --quiet 2>/dev/null; then
            log "$pkg installed successfully."
        elif $PYTHON -m pip install --user "$pkg" --quiet 2>/dev/null; then
            log "$pkg installed (--user) successfully."
        else
            err "Failed to install $pkg."
            return 1
        fi
    else
        log "$pkg is available."
    fi
}

PIP_OK=true
# Ensure pip exists
if ! $PYTHON -m pip --version &>/dev/null; then
    warn "pip not found. Attempting to install..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y -qq python3-pip 2>/dev/null
    elif $PYTHON -c "import ensurepip; ensurepip.bootstrap()" 2>/dev/null; then
        true
    else
        curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON 2>/dev/null || PIP_OK=false
    fi
fi

if [ "$PIP_OK" = true ] && $PYTHON -m pip --version &>/dev/null; then
    install_pkg pandas || exit 1
    install_pkg numpy  || exit 1
else
    # Check if they're already available even without pip
    if $PYTHON -c "import pandas; import numpy" 2>/dev/null; then
        log "pandas and numpy already available (pip missing but packages present)."
    else
        err "pip unavailable and packages missing. Shell fallback will be used."
        exit 1
    fi
fi

log "Environment ready. Python DQ checker can run."
echo "PYTHON_CMD=$PYTHON"
exit 0
