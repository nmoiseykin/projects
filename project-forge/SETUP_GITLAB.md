# Setup GitLab Repository

## Current Status

✅ **GitHub:** Working (repository exists, SSH key works)
❌ **GitLab:** SSH authentication failing

## Issue

The GitLab repository may not exist yet, or the SSH key needs to be verified.

## Solution: Create GitLab Repository

### Step 1: Create Repository on GitLab

1. Go to: https://gitlab.com/projects/new
2. Click "Create blank project"
3. Project name: `project-forge`
4. Visibility: Private (or Public)
5. **DO NOT** initialize with README
6. Click "Create project"

### Step 2: Verify SSH Key

1. Go to: https://gitlab.com/-/profile/keys
2. Verify your SSH key is listed:
   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINRHsvJASBZYiDjrOtI/i+FuokbHZkFll7izNIqgA+mC moiseykin@gmail.com
   ```
3. If not listed, add it:
   - Click "Add new key"
   - Paste the key above
   - Click "Add key"

### Step 3: Test Connection

```bash
ssh -T git@gitlab.com
```

Should return: `Welcome to GitLab, @nmoiseykin!`

### Step 4: Push to GitLab

Once repository is created:

```bash
cd ~/projects/project-forge
git push gitlab main
```

## Alternative: Push to GitHub Instead

If you prefer to push to GitHub (which already works), update the script:

```bash
# Edit auto-push-gitlab.sh
# Change: git push gitlab main
# To:     git push origin main
```

Or update the cron job to push to origin (GitHub) instead of gitlab.

## Current Configuration

- **GitHub (origin):** `git@github.com:nmoiseykin/project-forge.git` ✅ Working
- **GitLab (gitlab):** `git@gitlab.com:nmoiseykin/project-forge.git` ❌ Failing

