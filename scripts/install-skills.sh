#!/bin/bash
# scripts/install-skills.sh - Install or uninstall skills by symlinking/removing them to/from a target directory

set -e

# Get absolute path of this script's directory and the project's skills directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_SRC_DIR="$PROJECT_ROOT/skills"

# Print usage information
show_help() {
    echo "Usage: $0 [options] [target_directory]"
    echo ""
    echo "Options:"
    echo "  -d, --delete   Delete/uninstall skills from the target directory"
    echo "  -f, --force    Overwrite/remove existing symlinks/files without prompting"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Arguments:"
    echo "  target_directory  The directory to install/delete skills from."
    echo "                    Defaults to ~/.agent/skills if not specified."
    echo ""
    echo "Examples:"
    echo "  $0 ~/.agent/skills"
    echo "  $0 --delete ~/.agent/skills"
}

DELETE_MODE=false
FORCE=false
TARGET_DIR=""

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--delete)
            DELETE_MODE=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            show_help >&2
            exit 1
            ;;
        *)
            if [ -n "$TARGET_DIR" ]; then
                echo "Error: Multiple target directories specified: $TARGET_DIR and $1" >&2
                exit 1
            fi
            TARGET_DIR="$1"
            shift
            ;;
    esac
done

# Check if skills source directory exists
if [ ! -d "$SKILLS_SRC_DIR" ]; then
    echo "Error: Skills source directory not found at $SKILLS_SRC_DIR" >&2
    exit 1
fi

# Default target directory to ~/.agent/skills if not specified
if [ -z "$TARGET_DIR" ]; then
    TARGET_DIR="$HOME/.agent/skills"
fi

# Expand tilde ~ manually if present
if [[ "$TARGET_DIR" == ~* ]]; then
    TARGET_DIR="${TARGET_DIR/#\~/$HOME}"
fi

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    if [ "$DELETE_MODE" = true ]; then
        echo "Target directory $TARGET_DIR does not exist. Nothing to delete."
        exit 0
    else
        mkdir -p "$TARGET_DIR"
    fi
fi

# Resolve absolute path of target directory
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

# Counter for tracking actions
count=0

if [ "$DELETE_MODE" = true ]; then
    echo "Uninstalling skills..."
    echo "Source: $SKILLS_SRC_DIR"
    echo "Target: $TARGET_DIR"
    echo ""

    # Iterate over all skills in skills/
    for skill_path in "$SKILLS_SRC_DIR"/*; do
        if [ -d "$skill_path" ]; then
            skill_name=$(basename "$skill_path")
            dest_path="$TARGET_DIR/$skill_name"
            
            if [ -e "$dest_path" ] || [ -L "$dest_path" ]; then
                # Check if it points to the correct source
                is_correct_symlink=false
                if [ -L "$dest_path" ] && [ "$(readlink "$dest_path")" = "$skill_path" ]; then
                    is_correct_symlink=true
                fi
                
                if [ "$is_correct_symlink" = true ] || [ "$FORCE" = true ]; then
                    rm -rf "$dest_path"
                    echo "✓ Removed: $skill_name"
                    count=$((count+1))
                else
                    echo "Warning: Target is not a symlink to this project's skill: $dest_path"
                    read -p "Delete it anyway? [y/N] " -n 1 -r
                    echo ""
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        rm -rf "$dest_path"
                        echo "✓ Removed: $skill_name"
                        count=$((count+1))
                    else
                        echo "Skipped: $skill_name"
                    fi
                fi
            else
                echo "- $skill_name (not installed)"
            fi
        fi
    done

    echo ""
    echo "Successfully deleted $count skills from $TARGET_DIR."

else
    echo "Installing skills..."
    echo "Source: $SKILLS_SRC_DIR"
    echo "Target: $TARGET_DIR"
    echo ""

    # Iterate over all skills in skills/
    for skill_path in "$SKILLS_SRC_DIR"/*; do
        if [ -d "$skill_path" ]; then
            skill_name=$(basename "$skill_path")
            dest_path="$TARGET_DIR/$skill_name"
            
            # Check if the target exists
            if [ -e "$dest_path" ] || [ -L "$dest_path" ]; then
                if [ "$FORCE" = true ]; then
                    rm -rf "$dest_path"
                else
                    # If it's already a symlink pointing to the correct source, skip it
                    if [ -L "$dest_path" ] && [ "$(readlink "$dest_path")" = "$skill_path" ]; then
                        echo "✓ $skill_name (already linked)"
                        continue
                    fi
                    
                    echo "Warning: Target already exists: $dest_path"
                    read -p "Overwrite? [y/N] " -n 1 -r
                    echo ""
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        rm -rf "$dest_path"
                    else
                        echo "Skipped: $skill_name"
                        continue
                    fi
                fi
            fi
            
            # Create symbolic link
            ln -s "$skill_path" "$dest_path"
            echo "✓ $skill_name -> $skill_path"
            count=$((count+1))
        fi
    done

    echo ""
    echo "Successfully installed $count skills to $TARGET_DIR."
fi
