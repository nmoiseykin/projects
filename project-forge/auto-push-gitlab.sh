#!/bin/bash
# Auto-push script for GitHub/GitLab
# This script commits all changes and pushes to GitHub (origin) and GitLab (if configured)

# Don't exit on error - we want to log failures
set +e

# Change to project directory
cd /home/nmoiseykin/projects/project-forge

# Setup SSH for non-interactive environment (cron)
# Expand home directory (cron doesn't expand ~)
HOME_DIR="${HOME:-/home/nmoiseykin}"

# Find SSH key (try common locations)
SSH_KEY=""
for key in "$HOME_DIR/.ssh/id_rsa" "$HOME_DIR/.ssh/id_ed25519" "$HOME_DIR/.ssh/id_ecdsa" "$HOME_DIR/.ssh/id_dsa"; do
    if [ -f "$key" ]; then
        SSH_KEY="$key"
        break
    fi
done

# Configure SSH for GitLab
if [ -n "$SSH_KEY" ]; then
    export GIT_SSH_COMMAND="ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes"
else
    export GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new"
fi

# Ensure GitLab host key is in known_hosts
KNOWN_HOSTS="$HOME_DIR/.ssh/known_hosts"
if [ ! -f "$KNOWN_HOSTS" ] || ! grep -q "gitlab.com" "$KNOWN_HOSTS" 2>/dev/null; then
    mkdir -p "$HOME_DIR/.ssh"
    ssh-keyscan gitlab.com >> "$KNOWN_HOSTS" 2>/dev/null || true
    chmod 600 "$KNOWN_HOSTS" 2>/dev/null || true
fi

# Log file for tracking pushes
LOG_FILE="/home/nmoiseykin/projects/project-forge/logs/gitlab-push.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Starting auto-push to GitHub/GitLab..."

# Check if there are any changes
if git diff --quiet && git diff --cached --quiet; then
    log "No changes to commit"
    exit 0
fi

# Add all changes
git add -A

# Check if there are staged changes
if git diff --cached --quiet; then
    log "No changes to commit after staging"
    exit 0
fi

# Commit with timestamp
COMMIT_MSG="Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG" || {
    log "Error: Failed to commit changes"
    exit 1
}

# Push to GitHub (origin) - primary push
log "Pushing to GitHub (origin)..."
if [ -f "$HOME_DIR/.ssh/config" ]; then
    GITHUB_OUTPUT=$(git push origin main 2>&1)
else
    if [ -n "$SSH_KEY" ]; then
        GITHUB_OUTPUT=$(GIT_SSH_COMMAND="ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes" git push origin main 2>&1)
    else
        GITHUB_OUTPUT=$(git push origin main 2>&1)
    fi
fi
GITHUB_EXIT=$?

echo "$GITHUB_OUTPUT" | tee -a "$LOG_FILE"

if [ $GITHUB_EXIT -eq 0 ]; then
    log "Successfully pushed to GitHub"
else
    log "GitHub push failed: $GITHUB_OUTPUT"
fi

# Also try to push to GitLab if configured (optional)
if git remote get-url gitlab >/dev/null 2>&1; then
    log "Pushing to GitLab (gitlab)..."
    if [ -f "$HOME_DIR/.ssh/config" ]; then
        GITLAB_OUTPUT=$(git push gitlab main 2>&1)
    else
        if [ -n "$SSH_KEY" ]; then
            GITLAB_OUTPUT=$(GIT_SSH_COMMAND="ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes" git push gitlab main 2>&1)
        else
            GITLAB_OUTPUT=$(GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new" git push gitlab main 2>&1)
        fi
    fi
    GITLAB_EXIT=$?
    
    echo "$GITLAB_OUTPUT" | tee -a "$LOG_FILE"
    
    if [ $GITLAB_EXIT -eq 0 ]; then
        log "Successfully pushed to GitLab"
    else
        # Log GitLab errors but don't fail
        if echo "$GITLAB_OUTPUT" | grep -q "Permission denied\|repository.*not found"; then
            log "GitLab push failed (non-critical): $GITLAB_OUTPUT"
        else
            log "GitLab push failed: $GITLAB_OUTPUT"
        fi
    fi
else
    log "GitLab remote not configured, skipping"
fi

# Success if at least GitHub push worked
if [ $GITHUB_EXIT -eq 0 ]; then
    log "Auto-push completed successfully (pushed to GitHub)"
    exit 0
else
    log "Auto-push completed with errors (changes were committed locally)"
    exit 0
fi

