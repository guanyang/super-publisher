#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SKILL_ROOT/.venv"
REQUIREMENTS_FILE="$SKILL_ROOT/requirements.txt"
PYTHON_SCRIPT="$SCRIPT_DIR/make_stickers.py"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 1. Check/Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    log_success "Virtual environment created."
fi

# 2. Install Dependencies
# We use a marker file to avoid running pip install every time if requirements haven't changed
# But for simplicity and robustness, we'll just run pip install (pip is fast if satisfied)
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

log_info "Checking dependencies..."
"$PIP_BIN" install -q -r "$REQUIREMENTS_FILE"

# 3. Run the valid script
log_info "Running sticker maker..."
"$PYTHON_BIN" "$PYTHON_SCRIPT" "$@"
