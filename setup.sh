#!/usr/bin/env bash
# ── HailoRover: one-shot Pi setup + Hailo venv activation ──
#
#   bash setup.sh       full install (idempotent); prints an activation hint
#   source setup.sh     installs if needed, then activates the venv in this shell
#
# The hailo-apps clone lives inside this repo (hailo-apps/, gitignored) with
# its venv at hailo-apps/venv_hailo_apps. Steps:
#   1. hailo-apps install.sh (apt HailoRT/TAPPAS + venv + ~1.5 GB resources)
#   2. editable-install refresh (repairs absolute paths after a move)
#   3. server requirements (+ contextlib2/future for the hailoRT wheel)
#   4. pip install -e raspi/hailo-layer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HAILO_APPS_DIR="${HAILO_APPS_DIR:-$SCRIPT_DIR/hailo-apps}"
VENV="$HAILO_APPS_DIR/venv_hailo_apps"
MARKER="$VENV/.hailorover-setup-done"

SOURCED=0
if [ -n "$BASH_VERSION" ]; then
    [[ "${BASH_SOURCE[0]}" != "$0" ]] && SOURCED=1
elif [ -n "$ZSH_VERSION" ]; then
    [[ -o sourced ]] && SOURCED=1
fi

die() {
    echo "ERROR: $*" >&2
    if [ "$SOURCED" = 1 ]; then return 1; else exit 1; fi
}

install_all() {
    echo "══╡ HailoRover Setup ╞══"
    echo "Repo:        $SCRIPT_DIR"
    echo "hailo-apps:  $HAILO_APPS_DIR"

    if [ ! -d "$HAILO_APPS_DIR" ]; then
        die "hailo-apps not found at $HAILO_APPS_DIR — clone it inside the repo first:
  git clone https://github.com/hailo-ai/hailo-apps.git \"$SCRIPT_DIR/hailo-apps\""
    fi

    # 1) hailo-apps system install (re-runnable; resources already downloaded are skipped)
    echo
    echo "[1/4] hailo-apps install.sh (sudo — will prompt for password)..."
    ( cd "$HAILO_APPS_DIR" && sudo ./install.sh ) || die "install.sh failed"

    # 2) Repair/refresh the editable hailo-apps install — fixes absolute path
    #    pointers if the clone was moved. python -m pip sidesteps stale venv
    #    script shebangs left over from a move.
    echo "[2/4] Refreshing hailo-apps editable install..."
    source "$VENV/bin/activate"
    python -m pip install -e "$HAILO_APPS_DIR" --quiet || die "editable refresh failed"

    # 3) Server dependencies (+ hailoRT wheel deps that may be missing)
    echo "[3/4] Server requirements..."
    # hailoRT wheel deps first, so the requirements resolve without conflicts
    python -m pip install contextlib2 future --quiet || die "hailoRT deps failed"
    # scipy >=1.15 requires numpy>=2 — pin it down to stay on the numpy 1.x line
    if python -c "import scipy" 2>/dev/null; then
        python -m pip install "scipy>=1.13,<1.15" --quiet || die "scipy downgrade failed"
    fi
    python -m pip install -r "$SCRIPT_DIR/raspi/server/requirements.txt" --quiet || die "requirements install failed"

    # 4) The Option B inference layer
    echo "[4/4] hailo-layer..."
    python -m pip install -e "$SCRIPT_DIR/raspi/hailo-layer" --quiet || die "hailo-layer install failed"

    # Verify the constraints that matter at runtime
    echo
    echo "Verifying..."
    python - <<'EOF' || die "numpy constraint violated (HailoRT requires <2)"
import numpy as np
v = tuple(int(x) for x in np.__version__.split(".")[:2])
assert v[0] == 1, f"numpy {np.__version__} is >=2"
print(f"numpy {np.__version__} OK")
EOF
    python -c "import hailo; print('hailo import OK')" || die "import hailo failed"
    # The venv is created with --system-site-packages, so apt-installed typing
    # stubs (types-*) and apt tools (apt-listchanges) show up in pip check —
    # they are system noise, not venv problems. Filter them out.
    python -m pip check 2>&1 \
        | grep -vE "^(types-|apt-listchanges)" \
        | sed 's/^/pip check: /' || true

    touch "$MARKER"
    echo
    echo "══╡ Setup complete ╞══"
}

if [ "$SOURCED" = 1 ]; then
    if [ -f "$MARKER" ] && [ -d "$VENV" ]; then
        source "$VENV/bin/activate"
        echo "Activated: $VENV"
    else
        install_all || return 1
        source "$VENV/bin/activate" && echo "Activated: $VENV"
    fi
else
    install_all
    echo
    echo "Activate the venv in this shell with:  source setup.sh"
    echo "Verify:  hailo-smoke --hef-path yolov8m --input /dev/video0 --run-time 30"
fi
