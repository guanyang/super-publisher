#!/bin/bash
set -euo pipefail

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SKILL_DIR/.venv"

usable_python() {
    "$1" -c 'from PIL import Image, __version__; assert int(__version__.split(".")[0]) >= 10' >/dev/null 2>&1
}

if [ -x "$VENV_DIR/bin/python" ] && usable_python "$VENV_DIR/bin/python"; then
    exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/make_gif.py" "$@"
fi
if command -v python3 >/dev/null 2>&1 && usable_python "$(command -v python3)"; then
    exec "$(command -v python3)" "$SCRIPT_DIR/make_gif.py" "$@"
fi
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 with Pillow >= 10 is required." >&2
    exit 1
fi

GIF_CREATED_VENV=0
cleanup_failed_setup() {
    local status=$?
    if [ "$status" -ne 0 ] && [ "$GIF_CREATED_VENV" -eq 1 ]; then
        rm -rf -- "$VENV_DIR"
    fi
}
trap cleanup_failed_setup EXIT
if [ ! -e "$VENV_DIR" ]; then
    GIF_CREATED_VENV=1
    python3 -m venv "$VENV_DIR" >&2
elif [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Error: Existing $VENV_DIR is incomplete; repair it or provide a usable Python." >&2
    exit 1
fi
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check -r "$SKILL_DIR/requirements.txt" >&2
usable_python "$VENV_DIR/bin/python"
trap - EXIT
exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/make_gif.py" "$@"
