# Git Automation System - Design Document
**Date:** October 20, 2025
**Server:** iac1 (100.100.101.1)
**Purpose:** Mandatory automated git operations for Claude Code

---

## 🎯 Design Goals

Based on successful deployment automation (30x faster, 0 conflicts), apply same principles to git:

1. **Zero Manual Intervention** - Claude Code calls one function, git handles everything
2. **Intelligent Commit Messages** - AI-generated based on changes
3. **Automatic Branching** - Feature branches for new work
4. **Safety First** - Pre-commit validation, rollback capability
5. **Mandatory Enforcement** - Claude Code MUST use this for all commits
6. **Complete Audit Trail** - Track all commits in database

---

## 📊 Architecture (Mirror of Deployment System)

```
Claude Code Request
       ↓
MCP Tool: auto_git_commit({
  files: ["file1.js", "file2.md"],
  message: "optional custom message",
  branch: "auto-feature-xyz"
})
       ↓
Coordinator Agent (executeGitCommit)
       ↓
Git Helpers Module
  ├─ analyzeChanges() - AI analyzes diffs
  ├─ generateCommitMessage() - Smart message generation
  ├─ validateCommit() - Pre-commit checks
  ├─ executeCommit() - git add + commit
  ├─ executePush() - git push (optional)
  └─ rollbackCommit() - git reset if failure
       ↓
Database: git_commits table
       ↓
Return: { success, commitHash, branch, message }
```

---

## 🛠️ Components to Build

### 1. Git Helpers Module (`~/host-config-agent/agents/git-helpers.js`)

**Functions:**
```javascript
// Analyze what changed (git diff + git status)
export async function analyzeChanges(files = null) {
  // git status --porcelain
  // git diff for each file
  // Returns: { modified: [], added: [], deleted: [], diffs: {} }
}

// AI-powered commit message generation
export async function generateCommitMessage(changes, userMessage = null) {
  // If userMessage provided, use it
  // Otherwise: analyze changes + generate conventional commit message
  // Format: "feat: Add feature X" or "fix: Resolve issue Y"
  // Returns: { message, type: "feat|fix|docs|refactor|..." }
}

// Pre-commit validation
export async function validateCommit(files) {
  // Check: No merge conflicts
  // Check: No secrets in files (.env, credentials)
  // Check: Files exist and are readable
  // Returns: { valid: true/false, errors: [] }
}

// Execute git add + commit
export async function executeCommit(files, message, branch = null) {
  // If branch: git checkout -b branch || git checkout branch
  // git add files
  // git commit -m message
  // Returns: { success, commitHash, branch, output }
}

// Execute git push
export async function executePush(branch = null, remote = 'origin') {
  // git push origin branch
  // Returns: { success, output }
}

// Rollback commit (if push failed)
export async function rollbackCommit(commitHash) {
  // git reset HEAD~1
  // Returns: { success, message }
}

// Configure git user (one-time setup)
export async function configureGitUser(name, email) {
  // git config user.name "name"
  // git config user.email "email"
  // Returns: { success }
}
```

### 2. Coordinator Agent Enhancement (`~/host-config-agent/agents/coordinator-agent.js`)

**New Method:**
```javascript
async executeGitCommit(request) {
  const {
    files = null,  // null = all changes
    message = null,  // null = AI-generated
    branch = null,  // null = current branch
    push = false,  // auto-push after commit
    validate = true
  } = request;

  // 6-Step Process (mirror of executeDeployment):

  // 1. Analyze changes
  const changes = await GitHelpers.analyzeChanges(files);

  // 2. Validate (no secrets, no conflicts)
  if (validate) {
    const validation = await GitHelpers.validateCommit(files || changes.all);
    if (!validation.valid) {
      return { success: false, errors: validation.errors };
    }
  }

  // 3. Generate commit message (or use provided)
  const commitInfo = await GitHelpers.generateCommitMessage(changes, message);

  // 4. Execute commit
  const commitResult = await GitHelpers.executeCommit(
    files || changes.all,
    commitInfo.message,
    branch
  );

  // 5. Push if requested
  let pushResult = null;
  if (push && commitResult.success) {
    pushResult = await GitHelpers.executePush(branch);
    if (!pushResult.success) {
      // Rollback commit if push failed
      await GitHelpers.rollbackCommit(commitResult.commitHash);
      return { success: false, error: 'Push failed, commit rolled back' };
    }
  }

  // 6. Register in database
  this.db.prepare(`
    INSERT INTO git_commits (
      commit_hash, branch, message, files_changed,
      commit_type, pushed, committed_at, committed_by
    ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 'coordinator-agent')
  `).run(
    commitResult.commitHash,
    commitResult.branch,
    commitInfo.message,
    JSON.stringify(changes.all),
    commitInfo.type,
    push ? 1 : 0
  );

  // 7. Log decision
  await this.logDecision('git_commit', {
    files: changes.all,
    message: commitInfo.message,
    branch: commitResult.branch,
    pushed: push
  });

  return {
    success: true,
    commitHash: commitResult.commitHash,
    branch: commitResult.branch,
    message: commitInfo.message,
    filesChanged: changes.all.length,
    pushed: push
  };
}
```

**Additional Methods:**
```javascript
async getGitStatus() {
  // git status + recent commits
}

async getCommitHistory(limit = 10) {
  // Query git_commits table
}

async createBranch(branchName, baseBranch = 'master') {
  // git checkout -b branchName baseBranch
}
```

### 3. Database Schema (`/var/lib/host-config-agent/host_config.db`)

**New Table:**
```sql
CREATE TABLE IF NOT EXISTS git_commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_hash TEXT UNIQUE NOT NULL,
    branch TEXT NOT NULL,
    message TEXT NOT NULL,
    files_changed TEXT NOT NULL,  -- JSON array
    commit_type TEXT,  -- feat, fix, docs, refactor, etc
    pushed BOOLEAN DEFAULT 0,
    committed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    committed_by TEXT DEFAULT 'coordinator-agent',
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_git_commits_hash ON git_commits(commit_hash);
CREATE INDEX IF NOT EXISTS idx_git_commits_branch ON git_commits(branch);
```

### 4. MCP Tools (`~/host-config-agent/mcp/server.js`)

**4 New Tools:**

```javascript
{
  name: 'auto_git_commit',
  description: 'AUTOMATIC GIT COMMIT with AI message generation - MANDATORY for all commits',
  inputSchema: {
    type: 'object',
    properties: {
      files: {
        type: 'array',
        items: { type: 'string' },
        description: 'Files to commit (null = all changes)'
      },
      message: {
        type: 'string',
        description: 'Custom message (null = AI-generated)'
      },
      branch: {
        type: 'string',
        description: 'Branch name (null = current branch)'
      },
      push: {
        type: 'boolean',
        default: false,
        description: 'Auto-push after commit'
      }
    }
  }
}

{
  name: 'get_git_status',
  description: 'Get current git status and recent commits',
  inputSchema: {
    type: 'object',
    properties: {
      include_diff: {
        type: 'boolean',
        default: false,
        description: 'Include file diffs'
      }
    }
  }
}

{
  name: 'get_commit_history',
  description: 'Get commit history from database',
  inputSchema: {
    type: 'object',
    properties: {
      limit: {
        type: 'number',
        default: 10,
        description: 'Number of commits to return'
      },
      branch: {
        type: 'string',
        description: 'Filter by branch (null = all)'
      }
    }
  }
}

{
  name: 'create_git_branch',
  description: 'Create new git branch',
  inputSchema: {
    type: 'object',
    properties: {
      branch_name: {
        type: 'string',
        description: 'New branch name'
      },
      base_branch: {
        type: 'string',
        default: 'master',
        description: 'Base branch to branch from'
      }
    },
    required: ['branch_name']
  }
}
```

---

## 📋 MANDATORY POLICY (CLAUDE.md Integration)

**Add to ~/.claude/CLAUDE.md (after deployment policy):**

```markdown
## ⚡ MANDATORY GIT POLICY (NEW - Oct 20, 2025)
**IMPORTANT:** All git commits MUST use the Host Config Agent automatic commit system.

### REQUIRED: Use auto_git_commit for ALL commits

BEFORE committing ANY files, you MUST:
1. Call auto_git_commit MCP tool (analyzes changes, generates message, commits)
2. DO NOT manually run git add/commit commands
3. DO NOT manually write commit messages (unless specifically requested)
4. DO NOT manually create branches (use create_git_branch tool)

Exception: Emergency fixes only (with approval)

### Quick Commit Command
```javascript
// Commit all changes with AI-generated message
auto_git_commit({})

// Commit specific files with custom message
auto_git_commit({
  files: ["file1.js", "file2.md"],
  message: "feat: Add feature X"
})

// Commit and push to new branch
auto_git_commit({
  branch: "feature/new-feature",
  push: true
})
```

### Conventional Commit Types
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- refactor: Code refactoring
- test: Test changes
- chore: Maintenance tasks
```

---

## 🔒 Safety Features

1. **Secret Detection:**
   - Scan for `.env`, `credentials.json`, API keys
   - Block commit if secrets detected
   - Return error with file list

2. **Merge Conflict Detection:**
   - Check for conflict markers
   - Block commit if conflicts exist
   - Return error with conflict locations

3. **Pre-commit Validation:**
   - File existence check
   - Syntax validation (optional)
   - Size limits (warn if >10MB)

4. **Automatic Rollback:**
   - If push fails → rollback commit
   - Restore working directory
   - Return error with details

5. **Audit Trail:**
   - All commits tracked in database
   - Who, what, when, why
   - Link to deployment if applicable

---

## 📈 Benefits (Match Deployment System)

| Feature | Manual Git | Auto Git | Improvement |
|---------|-----------|----------|-------------|
| Time per commit | 2-5 min | 5-10 sec | **30x faster** |
| Message quality | Variable | Consistent | **100% conventional** |
| Secret leaks | Possible | Prevented | **0 leaks** |
| Commit tracking | None | Full audit | **100% tracked** |
| Rollback capability | Manual | Automatic | **Instant recovery** |

---

## 🚀 Implementation Steps

1. ✅ **Design Complete** (this document)
2. ⏳ **Implement git-helpers.js** (370 lines, similar to deployment-helpers.js)
3. ⏳ **Enhance coordinator-agent.js** (+280 lines, executeGitCommit method)
4. ⏳ **Update MCP server** (+120 lines, 4 new tools)
5. ⏳ **Create database table** (git_commits schema)
6. ⏳ **Update CLAUDE.md** (mandatory git policy)
7. ⏳ **Configure git user** (Wil Aroca, w.aroca@insaing.com)
8. ⏳ **Test with current changes** (commit this design doc + uncommitted files)
9. ⏳ **Restart host-config-agent.service**
10. ⏳ **Create enforcement docs** (GIT_POLICY_MANDATORY.md, GIT_QUICK_REFERENCE.md)

---

## 🎯 Success Criteria

- [x] Design complete and documented
- [ ] git-helpers.js implemented (370 lines)
- [ ] coordinator-agent.js enhanced (+280 lines)
- [ ] MCP server updated (+120 lines)
- [ ] Database schema created
- [ ] CLAUDE.md updated with mandatory policy
- [ ] Git user configured
- [ ] Test commit successful
- [ ] Service restarted
- [ ] Documentation complete

---

## 📞 Expected Usage

### Example 1: Auto-commit all changes
```javascript
// Claude Code sees modified files, reads MANDATORY GIT POLICY
auto_git_commit({})

// Returns:
{
  success: true,
  commitHash: "a1b2c3d",
  branch: "master",
  message: "feat: Add git automation system",
  filesChanged: 12,
  pushed: false
}
```

### Example 2: Feature branch workflow
```javascript
// Create feature branch
create_git_branch({ branch_name: "feature/port-automation" })

// Work on feature...

// Commit to feature branch
auto_git_commit({
  branch: "feature/port-automation",
  message: "feat: Implement automatic port assignment"
})

// Push feature branch
auto_git_commit({
  push: true
})
```

### Example 3: Custom commit message
```javascript
// User requests specific message
auto_git_commit({
  files: ["README.md", "docs/GUIDE.md"],
  message: "docs: Update documentation for v2.0"
})
```

---

## 🔍 AI Commit Message Generation

**Logic:**
```javascript
async function generateCommitMessage(changes, userMessage) {
  if (userMessage) return { message: userMessage, type: inferType(userMessage) };

  // Analyze changes
  const analysis = {
    newFiles: changes.added.length,
    modifiedFiles: changes.modified.length,
    deletedFiles: changes.deleted.length,
    fileTypes: categorizeFiles(changes.all),
    diffSummary: summarizeDiffs(changes.diffs)
  };

  // Determine commit type
  let type = 'chore';
  if (analysis.newFiles > 0 && analysis.fileTypes.includes('code')) type = 'feat';
  if (analysis.modifiedFiles > 0 && analysis.fileTypes.includes('code')) type = 'fix';
  if (analysis.fileTypes.every(t => t === 'docs')) type = 'docs';

  // Generate message
  const scope = inferScope(changes.all);
  const description = generateDescription(analysis);

  return {
    message: `${type}${scope}: ${description}`,
    type
  };
}
```

**Examples:**
- Added `deployment-helpers.js` → "feat: Add deployment automation module"
- Modified `CLAUDE.md` → "docs: Update deployment policy"
- Fixed `server.js` → "fix: Resolve MCP tool error"
- Deleted old files → "chore: Remove deprecated files"

---

**Made by Insa Automation Corp for OpSec**
**Design Date:** October 20, 2025 18:00 UTC
**Version:** 1.0 - Initial Design
