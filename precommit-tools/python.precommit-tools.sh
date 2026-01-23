#!/usr/bin/env bash
# precommit-tools.sh
# Führt: autoflake -> isort -> black -> flake8 -> bandit
# Optional: nutzt eine Python venv, prüft Installation der Tools, kann fehlende Tools in venv installieren,
# Optional: bei Erfolg git commit -m "$COMMIT_MSG"
#
# Usage:
#   ./precommit-tools.sh [--venv path/to/venv] [--install-missing] [--commit "message"] [--paths "."] [--skip-bandit]
#
set -eo pipefail

# Defaults
VENV=""
INSTALL_MISSING=0
COMMIT_MSG=""
PATHS="."            # Pfade/Globs, durch Leerzeichen getrennt; Standard: aktuelles Verzeichnis
SKIP_BANDIT=0

print_usage() {
  cat <<EOF
Usage: $0 [--venv VENV_PATH] [--install-missing] [--commit "message"] [--paths "path1 path2"] [--skip-bandit]

Options:
  --venv PATH           Use or create a Python venv at PATH and run tools from that venv's bin.
  --install-missing     If a required tool is missing in venv/PATH, pip install it into the venv.
  --commit "message"    If provided, stage all changes and create a commit with this message on success.
  --paths "p1 p2"       Space-separated list of paths to process (default: ".").
  --skip-bandit         Skip the bandit security scan.
  -h, --help            Show this help and exit.
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --venv)
      VENV="$2"; shift 2 ;;
    --install-missing)
      INSTALL_MISSING=1; shift ;;
    --commit)
      COMMIT_MSG="$2"; shift 2 ;;
    --paths)
      PATHS="$2"; shift 2 ;;
    --skip-bandit)
      SKIP_BANDIT=1; shift ;;
    -h|--help)
      print_usage; exit 0 ;;
    *)
      echo "Unknown arg: $1"; print_usage; exit 2 ;;
  esac
done

# Tools required (in order)
TOOLS=(autoflake isort black flake8 bandit)

# Resolve executables location (consider venv)
BIN_DIR=""
PYTHON_CMD="python3"

if [[ -n "$VENV" ]]; then
  # create venv if not exists
  if [[ ! -d "$VENV" ]]; then
    echo "Erstelle venv in: $VENV"
    $PYTHON_CMD -m venv "$VENV"
  fi
  # shellcheck disable=SC1090
  BIN_DIR="$VENV/bin"
  PIP_CMD="$VENV/bin/pip"
  PYTHON_CMD="$VENV/bin/python"
else
  BIN_DIR=""
  PIP_CMD="pip3"
fi

# Check command: preferring venv/bin if provided, else system PATH
cmd_path() {
  local cmd="$1"
  if [[ -n "$BIN_DIR" && -x "$BIN_DIR/$cmd" ]]; then
    echo "$BIN_DIR/$cmd"
    return 0
  fi
  if command -v "$cmd" >/dev/null 2>&1; then
    command -v "$cmd"
    return 0
  fi
  return 1
}

# Install missing into venv (if allowed)
install_into_venv() {
  local pkg="$1"
  if [[ -z "$PIP_CMD" ]]; then
    echo "Kein pip verfügbar zum Installieren von $pkg"
    return 1
  fi
  echo "Installiere $pkg in venv via $PIP_CMD ..."
  "$PIP_CMD" install --upgrade "$pkg"
}

# Verify tools (and optionally install)
declare -A FOUND
for t in "${TOOLS[@]}"; do
  # Skip bandit if requested
  if [[ "$t" == "bandit" && "$SKIP_BANDIT" -eq 1 ]]; then
    FOUND["$t"]="skipped"
    continue
  fi

  if cmd_path "$t" >/dev/null 2>&1; then
    FOUND["$t"]="ok"
  else
    FOUND["$t"]="missing"
    if [[ "$INSTALL_MISSING" -eq 1 && -n "$VENV" ]]; then
      # map command -> pip package name where different
      pkg_name="$t"
      # (autoflake package is "autoflake", bandit is "bandit")
      install_into_venv "$pkg_name" || {
        echo "Fehler beim Installieren von $pkg_name"
        exit 3
      }
      # recheck
      if cmd_path "$t" >/dev/null 2>&1; then
        FOUND["$t"]="ok"
      fi
    fi
  fi
done

# If any required tool still missing -> exit
MISSING=()
for t in "${TOOLS[@]}"; do
  if [[ "${FOUND[$t]}" == "missing" ]]; then
    MISSING+=("$t")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "Folgende Tools fehlen: ${MISSING[*]}"
  echo "Entweder --venv + --install-missing nutzen oder die Tools systemweit installieren."
  exit 4
fi

# Helper to run command, print header, and abort on fail
run_step() {
  echo
  echo "=== $1 ==="
  shift
  echo "+ $*"
  "$@"
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "Fehler in Schritt: $1 (exit $rc). Abbruch."
    exit $rc
  fi
}

# Run pipeline in order
# 1) autoflake: in-place cleanup (remove unused imports/vars)
AUTOFLAKE_CMD="$(cmd_path autoflake || true)"
ISORT_CMD="$(cmd_path isort || true)"
BLACK_CMD="$(cmd_path black || true)"
FLAKE8_CMD="$(cmd_path flake8 || true)"
BANDIT_CMD="$(cmd_path bandit || true)"

# Run commands per provided PATHS
echo "Verarbeite Pfade: $PATHS"

# Autoflake: rekursiv, in-place, remove unused imports & variables
if [[ -n "$AUTOFLAKE_CMD" ]]; then
  run_step "autoflake (remove unused imports/vars)" "$AUTOFLAKE_CMD" --in-place --remove-unused-variables --remove-all-unused-imports -r $PATHS
fi

# isort
if [[ -n "$ISORT_CMD" ]]; then
  run_step "isort (imports sortieren)" "$ISORT_CMD" $PATHS
fi

# black
if [[ -n "$BLACK_CMD" ]]; then
  run_step "black (formatieren)" "$BLACK_CMD" $PATHS
fi

# flake8
if [[ -n "$FLAKE8_CMD" ]]; then
  # flake8 sollte Fehler liefern, wenn Probleme existieren -> non-zero
  run_step "flake8 (linting)" "$FLAKE8_CMD" $PATHS
fi

# bandit (optional)
if [[ "$SKIP_BANDIT" -eq 0 && -n "$BANDIT_CMD" ]]; then
  # bandit -r . scans recursively
  run_step "bandit (security scan)" "$BANDIT_CMD" -r $PATHS
fi

echo
echo "Alle Checks erfolgreich."

# Optional: auto-commit
if [[ -n "$COMMIT_MSG" ]]; then
  echo "Stage changes and commit with message: $COMMIT_MSG"
  git add -A
  if git diff --cached --quiet; then
    echo "Keine Änderungen zum Committen."
  else
    git commit -m "$COMMIT_MSG"
    echo "Commit erstellt."
  fi
fi

exit 0
