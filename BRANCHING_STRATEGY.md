# Git Branching Strategy Guide
 
## 📋 Overview

Your project now follows a **Git Flow** branching model - the industry standard for production applications. This ensures code quality, stability, and safe deployments.

---

## 🌳 Branch Structure

### **1. `main` (Production Branch)**
- **Purpose**: Production-ready code only
- **When to use**: After thorough testing in UAT
- **Who can merge**: Project lead/senior developers
- **Protection**: Always protected, requires PR review
- **Stability**: MUST be stable and working 100%

### **2. `uat` (Testing/Staging Branch)**
- **Purpose**: User Acceptance Testing environment
- **When to use**: Test features before going to production
- **Who can merge**: Team leads can merge from dev
- **Protection**: Should be protected (recommended)
- **Stability**: Should be mostly stable, ready for QA testing

### **3. `dev` (Development Branch)**
- **Purpose**: Integration branch for developers
- **When to use**: Daily development, feature merging
- **Who can merge**: All developers can merge features here
- **Protection**: Optional protection
- **Stability**: May have bugs, this is testing ground

### **4. `feature/` (Feature Branches)**
- **Purpose**: Individual feature development
- **Naming**: `feature/user-authentication`, `feature/dark-mode`
- **Who uses**: Individual developers
- **Lifespan**: Created for a feature, deleted after merge

---

## 🔄 Proper Merge Flow (Downstream Model)

```
feature/xyz
    ↓
   dev (merge via Pull Request)
    ↓
   uat (merge when ready for testing)
    ↓
  main (merge when ready for production)
```

**Why this order matters:**
- Dev is the "sandbox" - closest to real code
- UAT is the "test bed" - simulates production
- Main is "truth" - what customers see

---

## 📝 Commands Used to Set Up Your Branches

```bash
# 1. Create the UAT branch from main
git branch uat main

# 2. Push UAT to remote repository
git push origin uat

# 3. Push main to remote (ensure it's synced)
git push origin main

# 4. Verify all branches exist locally
git branch -a

# 5. Verify all branches exist on GitHub
git branch -r
```

---

## 🎯 Setting Default Branch on GitHub

**Default branch** = the branch shown when someone visits your GitHub repo

1. Go to: `https://github.com/PatSam23/detective-L/settings`
2. Find **"Default branch"** section (left menu → Branches)
3. Click dropdown, select **`main`**
4. Click **Update**

**Why main?** Developers cloning your repo will get production code by default.

---

## 💼 Working with Features (Step-by-Step Example)

### Creating a feature branch:

```bash
# 1. Make sure you're on dev
git checkout dev

# 2. Update dev with latest changes
git pull origin dev

# 3. Create and switch to feature branch
git checkout -b feature/user-authentication

# 4. Make your changes
# Edit files, commit, etc.
git add .
git commit -m "feat: add user authentication"

# 5. Push your feature branch to GitHub
git push origin feature/user-authentication
```

### Merging feature back to dev:

```bash
# Option 1: Via GitHub (RECOMMENDED - Professional standard)
# 1. Go to your repo on GitHub
# 2. GitHub shows "Compare & pull request" button
# 3. Click it, add description
# 4. Teammates review
# 5. Merge via GitHub's "Merge pull request" button
# 6. Delete the feature branch

# Option 2: Via command line (if GitHub PR unavailable)
git checkout dev
git pull origin dev
git merge feature/user-authentication
git push origin dev
```

---

## 🚀 Promoting Code Through Branches

### Dev → UAT (when you want to test):

```bash
# 1. Make sure UAT is up to date
git checkout uat
git pull origin uat

# 2. Merge dev into UAT
git merge origin/dev

# 3. Push to remote
git push origin uat
```

### UAT → Main (when ready for production):

```bash
# 1. Make sure main is up to date
git checkout main
git pull origin main

# 2. Merge UAT into main
git merge origin/uat

# 3. Push to remote
git push origin main
```

---

## ⚠️ CRITICAL: Synchronization Protocol

**The #1 cause of branch divergence:** Not pulling from remote before merging.

### Before EVERY merge operation, follow this exact sequence:

```bash
# STEP 1: Always pull from remote first
git fetch origin                    # Update remote tracking branches
git checkout <target_branch>        # Switch to the branch you're merging INTO
git pull origin <target_branch>     # Get latest commits from GitHub

# STEP 2: Then do your merge
git merge origin/<source_branch>    # Merge the source branch

# STEP 3: Push immediately
git push origin <target_branch>     # Send changes back to GitHub

# STEP 4: Verify the merge succeeded
git log --oneline -5                # Show recent commits
```

**Example - Merging dev into uat:**
```bash
git fetch origin                    # 1. Refresh
git checkout uat                    # 2. Switch to uat
git pull origin uat                 # 3. Get latest uat from GitHub
git merge origin/dev                # 4. Merge dev
git push origin uat                 # 5. Push result
```

---

## 🔍 Your Ideal Workflow (Day-to-Day)

### When starting work on a new feature:

```bash
# 1. Ensure you're on dev and it's up to date
git checkout dev
git fetch origin
git pull origin dev

# 2. Create feature branch (ALWAYS from dev, NEVER from main)
git checkout -b feature/llm-caching

# 3. Work on the feature
# ... edit files, test, commit ...
git add .
git commit -m "feat: implement Redis caching layer"

# 4. Keep feature branch synced with dev while working
#    (Do this every day or before final push)
git fetch origin
git merge origin/dev  # Bring in any new changes from dev

# 5. When feature is DONE, push to GitHub
git push origin feature/llm-caching
```

### When submitting a feature (GitHub Pull Request):

```bash
# Go to GitHub → Compare & Pull Request
# Ensure:
# - Base branch = dev (NOT main)
# - Head branch = feature/your-feature-name
# - Add description of what you built
# - Request code review
# - Wait for approval, then merge on GitHub
# - GitHub will offer to delete the branch → click it
```

### When promoting dev → uat:

```bash
# Only do this when dev is tested and ready
git fetch origin                  # Get latest remote info
git checkout uat                  # Switch to uat
git pull origin uat               # Ensure uat is current
git merge origin/dev              # Bring dev changes into uat
git push origin uat               # Push to GitHub
```

### When promoting uat → main (for production release):

```bash
# Only do this after uat has been tested thoroughly
git fetch origin                  # Get latest remote info
git checkout main                 # Switch to main
git pull origin main              # Ensure main is current
git merge origin/uat              # Bring uat changes into main
git push origin main              # Push to GitHub (NOW LIVE)
```

---

## ✅ Prevention Checklist (Avoid Divergence)

Before every merge, verify these 4 things:

**1. Remote is up to date:**
```bash
git fetch origin
```

**2. You're on the correct target branch:**
```bash
git branch  # Shows current branch (*)
```

**3. Your branch is synced with remote:**
```bash
git status
# Should say: "Your branch is up to date with 'origin/branchname'"
# Should NOT say: "Your branch is behind..."
```

**4. You're merging from the right source:**
```bash
git log --oneline -3 origin/<source_branch>  # Verify commits exist
```

If anything fails these checks, STOP and fix it first.

---

## 🚨 Fixing Branch Divergence (If It Happens Again)

**If you see: "X commits ahead, Y commits behind"**

This means the branches have diverged. Fix it immediately:

```bash
# 1. Fetch latest from GitHub
git fetch origin

# 2. Check what's different
git log --oneline origin/main..origin/dev        # What's in dev NOT in main
git log --oneline origin/dev..origin/main        # What's in main NOT in dev

# 3. Align them (merge the branch with MORE commits into the one with FEWER)
# Usually: merge main into dev (or uat)
git checkout dev
git pull origin dev
git merge origin/main  # Brings main's commits into dev
git push origin dev

# 4. Verify they're aligned
git log --oneline origin/main..origin/dev  # Should be 0
git log --oneline origin/dev..origin/main  # Should be 0
```

---

## 🔐 Why This Prevents Problems

| Issue | Prevention |
|-------|-----------|
| Feature branch with old code | ALWAYS create feature from fresh dev (`git pull`) |
| Lost commits | ALWAYS merge `origin/` branches, not local ones |
| Diverged history | ALWAYS `git fetch` + `git pull` before merging |
| Accidental main changes | Feature → dev ONLY (not main), dev → uat, uat → main |
| Merge conflicts | Pull frequently, small commits, early merges |
| Remote not synced | Always push immediately after merge |

---

## 📊 Visual: Safe Merge Operation

```
START HERE
    ↓
git fetch origin        ← Get latest from GitHub
    ↓
git checkout <target>   ← Switch to where you're merging INTO
    ↓
git pull origin <target> ← Ensure you have latest code
    ↓
git merge origin/<source> ← Merge the source code
    ↓
git push origin <target> ← Send back to GitHub
    ↓
DONE ✅
```

**Follow this EVERY time. No exceptions.**

# 4. Test in UAT environment
# Run tests, QA review, etc.
```

### UAT → Main (when tested & ready):

```bash
# 1. Make sure main is up to date
git checkout main
git pull origin main

# 2. Merge UAT into main
git merge uat

# 3. Push to production
git push origin main

# 4. Create a tag (optional but recommended)
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

---

## 🛡️ Best Practices for Merging

### ✅ DO:

1. **Create Pull Requests (PRs)** instead of direct merges
   ```bash
   # After pushing feature branch, GitHub shows "Create PR" button
   ```

2. **Use descriptive commit messages**
   ```bash
   git commit -m "feat: add dark mode support for UI"
   git commit -m "fix: resolve button click handler issue"
   ```

3. **Merge via GitHub's UI** (not command line)
   - Easier to see changes
   - Teammates can review
   - Easier to revert if needed

4. **Delete merged feature branches**
   ```bash
   # Delete locally
   git branch -d feature/user-authentication
   
   # Delete remotely
   git push origin --delete feature/user-authentication
   ```

5. **Keep commits clean** - squash when appropriate
   - Many small commits → merge via "Squash and merge"
   - Keeps main branch history clean

6. **Test before merging** - always test your code
   - Run tests locally
   - Run in UAT environment
   - Get team review

### ❌ DON'T:

1. **Don't merge dev → main directly** - always go through UAT
2. **Don't commit directly to main or uat** - use PRs
3. **Don't delete main/uat/dev branches**
4. **Don't rebase public branches** - causes conflicts
5. **Don't force push** `git push -f` on shared branches

---

## 📊 Understanding the Workflow

```
Developer workflow:
┌─────────────────────────────────────────────┐
│  Developer 1          Developer 2           │
│  feature/auth    →    feature/payments      │
│       ↓                     ↓               │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─            │
│          dev (integration point)            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─            │
│       ↓ (when ready for testing)           │
│      uat (QA environment)                   │
│       ↓ (when QA approves)                  │
│      main (PRODUCTION - LIVE)               │
└─────────────────────────────────────────────┘
```

---

## 🔍 Useful Commands

```bash
# See all branches (local and remote)
git branch -a

# See branch last commit info
git branch -v

# Delete a local branch
git branch -d branch-name

# Delete a remote branch
git push origin --delete branch-name

# See which branches are merged
git branch --merged

# See which branches are NOT merged
git branch --no-merged

# Switch to a branch
git checkout branch-name

# Create and switch to new branch
git checkout -b new-branch-name

# See the commit history of a branch
git log branch-name --oneline
```

---

## 🎓 Example Timeline (Day in the life)

```
Morning:
├─ Create feature/user-dashboard from dev
├─ Commit code throughout day
└─ Push to origin

Afternoon:
├─ Create Pull Request on GitHub
├─ Team reviews
├─ Make requested changes
└─ Merge to dev via GitHub

Next Day:
├─ Merge dev → uat for testing
├─ QA tests the feature
└─ If bug found, fix in new feature branch

When Ready:
├─ UAT passes testing
├─ Merge uat → main
└─ Feature now in production ✅
```

---

## 📞 Current Branch Status

Your repository currently has:
- ✅ `main` - Production branch (ready)
- ✅ `uat` - Testing branch (ready)
- ✅ `dev` - Development branch (ready)
- ℹ️ `feature/*` - Create as needed for new features

**Default branch set to:** `main` (recommended)

---

## Quick Reference Card

| Branch | Purpose | Protection | Who | Next Step |
|--------|---------|-----------|-----|-----------|
| main | Production | 🔒 YES | Lead | Deploy to users |
| uat | Testing | ✓ Recommended | QA | Test & merge to main |
| dev | Development | ✓ Recommended | All devs | Merge features here |
| feature/* | Feature work | Optional | Individual | PR to dev |

---

## 🎯 Your Next Steps

1. Set `main` as default branch on GitHub (if not done)
2. Add branch protection rules (recommended):
   - Require PR reviews for main/uat
   - Require status checks to pass
3. Start using feature branches for new work
4. Follow the merge flow: feature → dev → uat → main

**Questions?** This guide covers production-standard workflows! 🚀
