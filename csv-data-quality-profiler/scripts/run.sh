#!/usr/bin/env bash
# ============================================================================
# CSV Data Quality Profiler — Smart runner
# Finds Python 3.8+, ensures pandas/numpy, then runs the checker.
# If Python/deps can't be set up, exits with a clear error.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ARGS=("$@")

# --- Find Python 3.8+ ---
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
    echo -e "${RED}[runner]${NC} Python 3.8+ not found. Please install Python first."
    echo -e "${RED}[runner]${NC}   Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo -e "${RED}[runner]${NC}   macOS:         brew install python3"
    echo -e "${RED}[runner]${NC}   Fedora:        sudo dnf install python3 python3-pip"
    exit 1
fi

# --- Check/install pandas + numpy ---
if ! $PYTHON -c "import pandas; import numpy" 2>/dev/null; then
    echo -e "${YELLOW}[runner]${NC} pandas/numpy not found. Running setup..."
    if bash "$SCRIPT_DIR/setup.sh"; then
        # Re-check after setup
        if ! $PYTHON -c "import pandas; import numpy" 2>/dev/null; then
            echo -e "${RED}[runner]${NC} Setup completed but packages still unavailable. Check pip output above."
            exit 1
        fi
    else
        echo -e "${RED}[runner]${NC} Setup failed. Install manually: pip install pandas numpy"
        exit 1
    fi
fi

echo -e "${GREEN}[runner]${NC} Using $($PYTHON --version 2>&1)"
$PYTHON "$SCRIPT_DIR/csv_dq_report.py" "${ARGS[@]}"
