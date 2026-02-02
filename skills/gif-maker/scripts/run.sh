#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SKILL_DIR/.venv"

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    # Install dependencies
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    if [ -f "$SKILL_DIR/requirements.txt" ]; then
        pip install -r "$SKILL_DIR/requirements.txt"
    fi
else
    source "$VENV_DIR/bin/activate"
fi

# Run the python script with all passed arguments
python3 "$SCRIPT_DIR/make_gif.py" "$@"
