#!/usr/bin/env python3
"""
Universal runner for Toutiao Publisher skill scripts
Ensures all scripts run with the correct virtual environment
"""

import os
import sys
import subprocess
import hashlib
import json
import signal
from pathlib import Path


def get_venv_python():
    """Get the virtual environment Python executable"""
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"

    if os.name == "nt":  # Windows
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        venv_python = venv_dir / "bin" / "python"

    return venv_python


def requirements_digest(requirements_file=None):
    skill_dir = Path(__file__).parent.parent
    path = Path(requirements_file or skill_dir / "requirements.txt")
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def requirements_are_current(venv_python):
    marker = Path(venv_python).parent.parent / ".requirements.sha256"
    try:
        return marker.read_text(encoding="utf-8").strip() == requirements_digest()
    except OSError:
        return False


def normalize_returncode(returncode):
    return 128 + abs(returncode) if returncode < 0 else returncode


def exit_with_error(status, message, json_mode=False, exit_code=1):
    if json_mode:
        print(
            json.dumps(
                {"ok": False, "status": status, "message": message},
                ensure_ascii=False,
            )
        )
        print(f"❌ {message}", file=sys.stderr)
    else:
        print(f"❌ {message}")
    raise SystemExit(exit_code)


def ensure_venv(json_mode=False):
    """Ensure virtual environment exists"""
    skill_dir = Path(__file__).parent.parent
    setup_script = skill_dir / "scripts" / "setup_environment.py"
    venv_python = get_venv_python()

    environment_ready = (
        venv_python.is_file()
        and os.access(venv_python, os.X_OK)
        and requirements_are_current(venv_python)
    )
    if not environment_ready:
        output = sys.stderr if json_mode else sys.stdout
        print("🔧 Preparing the skill virtual environment...", file=output)
        print("   This may take a minute...", file=output)

        try:
            result = subprocess.run(
                [sys.executable, str(setup_script)],
                stdout=sys.stderr if json_mode else None,
            )
        except OSError as e:
            exit_with_error(
                "environment_setup_failed",
                f"Failed to start environment setup: {e}",
                json_mode=json_mode,
            )
        if result.returncode != 0:
            exit_with_error(
                "environment_setup_failed",
                "Failed to set up the Skill environment",
                json_mode=json_mode,
            )

        venv_python = get_venv_python()
        if not (venv_python.is_file() and os.access(venv_python, os.X_OK)):
            exit_with_error(
                "environment_setup_failed",
                f"Virtual environment Python is unavailable: {venv_python}",
                json_mode=json_mode,
            )

        print("✅ Environment ready!", file=output)

    return venv_python


def main():
    """Main runner"""
    if len(sys.argv) < 2:
        print("Usage: python3 run.py <script_name> [args...]")
        print("\nAvailable scripts:")
        print("  auth_manager.py     - Handle authentication")
        print("  publisher.py        - Publish article")
        print("  cleanup_manager.py  - Clean up skill data")
        sys.exit(1)

    script_name = sys.argv[1]
    script_args = sys.argv[2:]
    json_mode = "--json" in script_args

    # Handle both "scripts/script.py" and "script.py" formats
    if script_name.startswith("scripts/"):
        # Remove the scripts/ prefix if provided
        script_name = script_name[8:]  # len('scripts/') = 8

    # Ensure .py extension
    if not script_name.endswith(".py"):
        script_name += ".py"

    # Get script path
    skill_dir = Path(__file__).parent.parent
    script_path = skill_dir / "scripts" / script_name

    if not script_path.exists():
        exit_with_error(
            "script_not_found",
            f"Script not found: {script_path}",
            json_mode=json_mode,
        )

    # Ensure venv exists and get Python executable
    venv_python = ensure_venv(json_mode=json_mode)

    # Build command
    cmd = [str(venv_python), str(script_path)] + script_args

    # Run the script
    process = None
    try:
        process = subprocess.Popen(
            cmd,
            start_new_session=os.name != "nt",
        )
        sys.exit(normalize_returncode(process.wait()))
    except KeyboardInterrupt:
        output = sys.stderr if json_mode else sys.stdout
        print(
            "\n⚠️ Interrupt received; waiting for the Skill process to finish...",
            file=output,
        )
        if process is None:
            sys.exit(130)
        if os.name != "nt":
            process.send_signal(signal.SIGINT)
        try:
            sys.exit(normalize_returncode(process.wait(timeout=30)))
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait()
            exit_with_error(
                "interrupted",
                "Skill process did not finish after the interrupt",
                json_mode=json_mode,
                exit_code=130,
            )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
