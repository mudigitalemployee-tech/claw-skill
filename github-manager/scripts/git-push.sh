#!/usr/bin/env bash
set -euo pipefail

# Git Push & PR Script
# Usage:
#   git-push.sh <folder> [--branch <name>] [--message <commit-msg>] [--pr] [--pr-title <title>] [--pr-body <body>] [--base <base-branch>]
#
# Default behavior: create a new branch from current branch, commit all changes, push, optionally open PR.
# With --branch: stash → checkout branch → pull → apply stash → commit → push.

FOLDER=""
BRANCH=""
MESSAGE=""
OPEN_PR=false
PR_TITLE=""
PR_BODY=""
BASE_BRANCH=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --branch) BRANCH="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    --pr) OPEN_PR=true; shift ;;
    --pr-title) PR_TITLE="$2"; shift 2 ;;
    --pr-body) PR_BODY="$2"; shift 2 ;;
    --base) BASE_BRANCH="$2"; shift 2 ;;
    *) FOLDER="$1"; shift ;;
  esac
done

if [[ -z "$FOLDER" ]]; then
  echo "ERROR: No folder specified" >&2
  exit 1
fi

cd "$FOLDER"

# Verify it's a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "ERROR: $FOLDER is not a git repository" >&2
  exit 1
fi

# Check for gh CLI
if ! command -v gh &>/dev/null; then
  echo "ERROR: gh CLI not installed. Install with: sudo apt-get install -y gh" >&2
  exit 1
fi

# Check gh auth
if ! gh auth status &>/dev/null 2>&1; then
  echo "ERROR: gh CLI not authenticated. Run: gh auth login" >&2
  exit 1
fi

# Detect remote
REMOTE=$(git remote | head -1)
if [[ -z "$REMOTE" ]]; then
  echo "ERROR: No git remote configured" >&2
  exit 1
fi
echo "INFO: Using remote '$REMOTE'"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "INFO: Current branch: $CURRENT_BRANCH"

# Detect default branch for PR base
if [[ -z "$BASE_BRANCH" ]]; then
  BASE_BRANCH=$(git remote show "$REMOTE" 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}' || echo "main")
fi

if [[ -n "$BRANCH" ]]; then
  # ── Explicit branch mode: stash → checkout → pull → apply → commit → push ──
  echo "INFO: Explicit branch mode → $BRANCH"

  # Stash any uncommitted changes
  STASH_MSG="git-push-pr-auto-stash-$(date +%s)"
  git stash push -m "$STASH_MSG" --include-untracked 2>/dev/null || true
  STASHED=$(git stash list | grep -c "$STASH_MSG" || true)

  # Checkout target branch (create if doesn't exist)
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git checkout "$BRANCH"
  elif git show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH"; then
    git checkout -b "$BRANCH" "$REMOTE/$BRANCH"
  else
    git checkout -b "$BRANCH"
  fi

  # Pull latest
  git pull "$REMOTE" "$BRANCH" --rebase 2>/dev/null || true

  # Apply stash if we stashed
  if [[ "$STASHED" -gt 0 ]]; then
    git stash pop || {
      echo "WARN: Stash apply had conflicts. Resolve manually." >&2
      exit 1
    }
  fi
else
  # ── Default mode: create new branch ──
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  BRANCH="feature/${CURRENT_BRANCH}-${TIMESTAMP}"
  echo "INFO: Creating new branch: $BRANCH"
  git checkout -b "$BRANCH"
fi

# Stage all changes
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
  echo "INFO: No changes to commit"
  exit 0
fi

# Generate commit message if not provided
if [[ -z "$MESSAGE" ]]; then
  # Summarize changes
  CHANGED_FILES=$(git diff --cached --name-only | head -20)
  FILE_COUNT=$(git diff --cached --name-only | wc -l)
  MESSAGE="Update ${FILE_COUNT} file(s): $(echo "$CHANGED_FILES" | head -3 | tr '\n' ', ' | sed 's/,$//')"
fi

echo "INFO: Committing with message: $MESSAGE"
git commit -m "$MESSAGE"

# Push
echo "INFO: Pushing to $REMOTE/$BRANCH"
git push -u "$REMOTE" "$BRANCH"

# Open PR if requested
if [[ "$OPEN_PR" == true ]]; then
  if [[ -z "$PR_TITLE" ]]; then
    PR_TITLE="$MESSAGE"
  fi
  echo "INFO: Creating PR: $PR_TITLE (base: $BASE_BRANCH)"
  if [[ -n "$PR_BODY" ]]; then
    gh pr create --title "$PR_TITLE" --body "$PR_BODY" --base "$BASE_BRANCH"
  else
    gh pr create --title "$PR_TITLE" --body "" --base "$BASE_BRANCH"
  fi
fi

echo "DONE: Successfully pushed $BRANCH to $REMOTE"
