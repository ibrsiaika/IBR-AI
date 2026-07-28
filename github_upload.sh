#!/bin/bash
# IBR Platform — GitHub Upload Helper
# This script helps upload the IBR Platform to GitHub safely.
# NEVER hardcodes tokens. Uses git credential helper.
#
# Usage:
#   ./github_upload.sh setup    # Configure git remote
#   ./github_upload.sh push     # Push with approval gate
#   ./github_upload.sh status   # Show push summary

set -e

REPO_OWNER="ibrsiaika"
REPO_NAME="ibr-platform"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
PROJECT_DIR="/home/z/my-project/ibr-platform"

echo "=============================================="
echo "IBR Platform — GitHub Upload Helper"
echo "=============================================="
echo "Repository: ${REPO_OWNER}/${REPO_NAME}"
echo "Project:    ${PROJECT_DIR}"
echo ""

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory does not exist: $PROJECT_DIR"
    echo "Create it first by following the MASTER_BUILD_PROMPT.md"
    exit 1
fi

cd "$PROJECT_DIR"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "ERROR: Git is not initialized in $PROJECT_DIR"
    echo "Run: cd $PROJECT_DIR && git init"
    exit 1
fi

case "${1:-help}" in

    setup)
        echo "=== SETUP ==="
        echo ""
        echo "This will configure the git remote for the IBR Platform repository."
        echo ""
        echo "PREREQUISITES:"
        echo "  1. Create the repository on GitHub:"
        echo "     - Go to: https://github.com/new"
        echo "     - Owner: ${REPO_OWNER}"
        echo "     - Name: ${REPO_NAME}"
        echo "     - Visibility: Private"
        echo "     - Do NOT initialize with README"
        echo ""
        echo "  2. Revoke the OLD token (compromised in chat):"
        echo "     - Go to: https://github.com/settings/tokens"
        echo "     - DELETE the old compromised token (ghp_XXXX...)"
        echo ""
        echo "  3. Create a NEW token:"
        echo "     - Go to: https://github.com/settings/tokens/new"
        echo "     - Note: ibr-platform-upload"
        echo "     - Scopes: repo (full)
        echo "     - Expiration: 30 days"
        echo "     - Copy the token (starts with ghp_)"
        echo "     - DO NOT share it in chat or commit it to git"
        echo ""
        read -p "Have you completed all 3 prerequisites? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Please complete the prerequisites first."
            exit 1
        fi
        echo ""
        echo "Configuring git remote..."
        git remote remove origin 2>/dev/null || true
        git remote add origin "$REPO_URL"
        git branch -M main
        echo ""
        echo "Configuring credential helper..."
        git config --global credential.helper store
        echo ""
        echo "=== SETUP COMPLETE ==="
        echo ""
        echo "On your first push, Git will ask for:"
        echo "  Username: ${REPO_OWNER}"
        echo "  Password: <paste your NEW token here>"
        echo ""
        echo "The token will be stored in ~/.git-credentials (chmod 600)"
        echo "Future pushes will not require re-entering the token."
        echo ""
        echo "To push, run: ./github_upload.sh push"
        ;;

    push)
        echo "=== PUSH SUMMARY ==="
        echo ""
        echo "Commits to push:"
        git log origin/main..HEAD --oneline 2>/dev/null || git log --oneline -10
        echo ""
        echo "Files changed:"
        git diff --stat origin/main..HEAD 2>/dev/null || git diff --stat HEAD~10..HEAD
        echo ""
        echo "Test status:"
        if [ -d "tests" ]; then
            echo "  (Run 'pytest tests/' to verify tests pass before pushing)"
        else
            echo "  No tests directory found"
        fi
        echo ""
        echo "Security check (secrets in code):"
        SECRET_FOUND=$(grep -rn "ghp_\|sk-ant\|sk-proj\|password\s*=" \
            --include="*.py" --include="*.ts" --include="*.yaml" --include="*.json" \
            --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir="__pycache__" \
            . 2>/dev/null | head -5 || echo "none")
        if [ "$SECRET_FOUND" != "none" ] && [ -n "$SECRET_FOUND" ]; then
            echo "  ⚠️  POTENTIAL SECRETS FOUND:"
            echo "$SECRET_FOUND"
            echo "  Review these before pushing!"
        else
            echo "  ✅ No secrets detected"
        fi
        echo ""
        echo "=============================================="
        echo ""
        read -p "Type 'PUSH APPROVED' to push to GitHub, or anything else to cancel: " approval
        echo ""
        if [ "$approval" = "PUSH APPROVED" ]; then
            echo "Pushing to ${REPO_URL}..."
            git push -u origin main
            echo ""
            echo "✅ Push successful!"
            echo "View at: https://github.com/${REPO_OWNER}/${REPO_NAME}"
        else
            echo "❌ Push cancelled."
            echo "Address any concerns, then run this script again."
        fi
        ;;

    status)
        echo "=== GIT STATUS ==="
        echo ""
        echo "Branch: $(git branch --show-current)"
        echo "Remote: $(git remote -v | head -1)"
        echo ""
        echo "Unpushed commits:"
        git log origin/main..HEAD --oneline 2>/dev/null || echo "  (no remote configured or no unpushed commits)"
        echo ""
        echo "Uncommitted changes:"
        git status --short
        echo ""
        echo "Recent commits:"
        git log --oneline -5
        ;;

    *)
        echo "Usage: $0 {setup|push|status}"
        echo ""
        echo "  setup  - Configure git remote (run once)"
        echo "  push   - Push to GitHub with approval gate"
        echo "  status - Show git status and unpushed commits"
        exit 1
        ;;

esac
