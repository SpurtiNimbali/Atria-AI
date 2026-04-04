#!/usr/bin/env bash
# Creates github.com/<you>/TreeHacks (or name you pass) and pushes this repo.
# One-time setup: run `gh auth login` first (install: brew install gh).
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI:  brew install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Log in to GitHub (browser or token):"
  echo "  gh auth login"
  exit 1
fi

REPO_NAME="${1:-TreeHacks}"

if git remote get-url origin >/dev/null 2>&1; then
  echo "Removing existing origin ($(git remote get-url origin))"
  git remote remove origin
fi

echo "Creating public repo ${REPO_NAME} and pushing main..."
gh repo create "${REPO_NAME}" --public --source=. --remote=origin --push \
  --description "Atria AI — discharge caregiver copilot (educational; not medical advice)"

echo "Done: $(git remote get-url origin)"
