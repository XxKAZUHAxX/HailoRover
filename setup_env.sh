#!/usr/bin/env bash
# ── HailoRover: activate the shared Hailo venv without leaving the repo ──
#
# The venv lives in the hailo-apps clone (~/hailo-apps, created by its install.sh).
# hailo-apps' own setup_env.sh uses pwd-relative paths, so it only works when
# sourced from inside ~/hailo-apps. This wrapper activates the same venv from
# anywhere. The GStreamer pipeline apps self-load /usr/local/hailo/resources/.env,
# so no extra env vars are required.
#
# Usage: source setup_env.sh
# Override venv location with: HAILO_APPS_VENV=/path/to/venv_hailo_apps

if [ -z "$BASH_VERSION" ] && [ -z "$ZSH_VERSION" ]; then
    echo "This script must be sourced, not executed:  source setup_env.sh" >&2
    exit 1
fi

VENV="${HAILO_APPS_VENV:-$HOME/Documents/Public Repositories/hailo-apps/venv_hailo_apps}"

if [ -d "$VENV" ]; then
    source "$VENV/bin/activate"
    echo "Activated: $VENV"
else
    echo "Venv not found: $VENV" >&2
    echo "Run install.sh from ~/hailo-apps first (see raspi/docs/hailo-setup.md)." >&2
    return 1 2>/dev/null || exit 1
fi
