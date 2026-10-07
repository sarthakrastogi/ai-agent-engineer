#!/usr/bin/env sh
# Thin wrapper: ./install.sh --harness <claude|codex|cursor|opencode|gemini> [--scope user] [--uninstall]
exec python3 "$(dirname "$0")/scripts/install.py" "$@"
