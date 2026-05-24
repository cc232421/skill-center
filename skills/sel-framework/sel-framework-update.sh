#!/usr/bin/env bash
set -euo pipefail
RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; BLUE=$'\033[0;34m'; RESET=$'\033[0m'
report() { echo -e "${BLUE}[sel-update]${RESET} $*"; }
pass()  { echo -e "${GREEN}✓${RESET} $*"; }
fail()  { echo -e "${RED}✗${RESET} $*"; }
warn()  { echo -e "${YELLOW}!${RESET} $*"; }
info()  { echo "  $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="${1:-"$SCRIPT_DIR"}"
cd "$SKILL_DIR"

echo ""
echo -e "${BLUE}══ sel-framework update ══${RESET}"
echo ""
info "skill: $SKILL_DIR"
info "branch: $(git branch --show-current 2>/dev/null || echo '?')"
info "commit:  $(git rev-parse --short HEAD 2>/dev/null || echo '?')"
echo ""

report "Stashing local changes..."
if ! git diff --quiet 2>/dev/null; then
    git stash push -m "sel-framework-update $(date -u +%Y%m%d%H%M%S)" -- \
        "*.py" "*.md" "*.json" "conftest.*" ".gitignore" \
        2>/dev/null && pass "Local changes stashed" || warn "Stash failed (continuing)"
else
    info "No local changes to stash"
fi

report "Pulling latest..."
git fetch origin --quiet
MERGE_RESULT=$(git pull --no-edit origin HEAD 2>&1) && pass "Pulled latest" || { fail "Pull failed: $MERGE_RESULT"; exit 1; }

COMMITS_AHEAD=$(git log origin/HEAD..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
[[ "$COMMITS_AHEAD" -gt 0 ]] && warn "Local is $COMMITS_AHEAD commit(s) ahead of remote" || pass "Up to date with remote"

report "Running pytest..."
PYTEST_OUTPUT=$(python -m pytest -q 2>&1)
PYTEST_EXIT=$?
if [[ $PYTEST_EXIT -eq 0 ]]; then
    PASSED=$(echo "$PYTEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+')
    pass "Tests: $PASSED passed"
    echo ""
    pass "sel-framework update complete"
    echo ""
else
    echo "$PYTEST_OUTPUT" | tail -5 | while IFS= read -r line; do warn "  $line"; done
    fail "Tests failed (exit $PYTEST_EXIT)"
    exit 1
fi
