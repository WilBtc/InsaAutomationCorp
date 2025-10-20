# Documentation Automation System - Design
**Date:** October 20, 2025 19:00 UTC
**Server:** iac1 (100.100.101.1)
**Purpose:** Automatic documentation updates with version sync and AI content generation

---

## 🎯 Design Goals

1. **Automatic Version Sync** - Update version numbers across all docs
2. **Automatic Timestamp Updates** - Keep "Last Updated" fields current
3. **AI Content Generation** - Generate changelog entries, status updates
4. **Broken Link Detection** - Find and report broken links
5. **Consistency Checking** - Ensure documentation consistency
6. **Minimal Manual Intervention** - 80% reduction in manual doc updates

---

## 📊 Architecture

```
Claude Code/User Request
       ↓
MCP Tool: auto_update_docs({
  files: ["CLAUDE.md", "README.md"],
  version_bump: "minor",      // major, minor, patch
  update_content: true,       // AI-generate updates
  check_links: true,          // Validate links
  sync_all: true             // Sync related docs
})
       ↓
Coordinator Agent (executeDocsUpdate)
       ↓
Docs Helpers Module
  ├─ findDocFiles() - Discover all .md files
  ├─ parseVersion() - Extract version from docs
  ├─ bumpVersion() - Increment version
  ├─ updateTimestamps() - Update dates
  ├─ generateChangelog() - AI changelog
  ├─ checkLinks() - Validate URLs
  ├─ syncRelatedDocs() - Update related files
  └─ validateMarkdown() - Check syntax
       ↓
Database: docs_updates table
       ↓
Auto Git Commit (via auto_git_commit)
       ↓
Return: { success, filesUpdated, newVersion }
```

---

## 🛠️ Components to Build

### 1. Docs Helpers Module (`docs-helpers.js`)

```javascript
// Find all documentation files
export async function findDocFiles(baseDir = '/home/wil') {
  // Patterns: README.md, CLAUDE.md, *_COMPLETE.md, *_GUIDE.md
  // Exclude: node_modules, .git, venv
}

// Parse version from documentation
export async function parseVersion(filePath) {
  // Formats: "Version: 7.2", "v7.2", "# v7.2"
  // Return: { major, minor, patch, raw }
}

// Bump version number
export function bumpVersion(currentVersion, bumpType = 'minor') {
  // major: 7.2 → 8.0
  // minor: 7.2 → 7.3
  // patch: 7.2.1 → 7.2.2
}

// Update timestamps in documentation
export async function updateTimestamps(filePath, newDate = new Date()) {
  // Patterns: "Updated: Oct 20, 2025", "Date: 2025-10-20"
  // Format: "October 20, 2025 19:00 UTC"
}

// AI-generate changelog entry
export async function generateChangelog(changes, context) {
  // Analyze recent commits (via git_commits table)
  // Generate bullet points
  // Format: "- Added git automation system"
}

// Check for broken links
export async function checkLinks(filePath) {
  // Find all markdown links: [text](url)
  // Validate: file:// links exist, http:// links respond
  // Return: { valid: [], broken: [] }
}

// Sync related documentation files
export async function syncRelatedDocs(primaryFile, updates) {
  // If CLAUDE.md updated → update README.md references
  // If version bumped → update all docs with same version
}

// Validate markdown syntax
export async function validateMarkdown(filePath) {
  // Check: Headers, lists, code blocks, tables
  // Return: { valid: boolean, errors: [] }
}

// Extract sections from markdown
export async function extractSections(filePath) {
  // Parse headers, identify sections
  // Return: { sections: [{ level, title, content, lineStart, lineEnd }] }
}

// Update specific section
export async function updateSection(filePath, sectionTitle, newContent) {
  // Find section by title
  // Replace content
  // Preserve formatting
}
```

---

## 📋 Documentation Files to Track

### Critical Files (Always Sync)
```yaml
Primary:
  - ~/.claude/CLAUDE.md                    # Version: 7.2 → 7.3
  - ~/host-config-agent/README.md          # Main docs
  - ~/insa-crm-platform/README.md          # Platform docs

Status Reports (Auto-generate):
  - ~/AUTO_PORT_ASSIGNMENT_IMPLEMENTATION_COMPLETE.md
  - ~/GIT_AUTOMATION_IMPLEMENTATION_COMPLETE.md
  - ~/DOCS_AUTOMATION_IMPLEMENTATION_COMPLETE.md
  - ~/SERVICES_TO_ADD_TO_AUTOMATION_SYSTEM.md

Quick References (Auto-sync):
  - ~/DEPLOYMENT_QUICK_REFERENCE.md
  - ~/.claude/GIT_QUICK_REFERENCE.md
  - ~/.claude/MCP_QUICK_REFERENCE.md

Agent Docs:
  - ~/host-config-agent/START_HERE.md
  - ~/host-config-agent/QUICKSTART.md
  - ~/host-config-agent/ARCHITECTURE.txt
```

---

## 🔧 MCP Tools (3 New Tools)

### Tool 1: `auto_update_docs` (Primary Tool)
```javascript
{
  name: 'auto_update_docs',
  description: 'AUTOMATIC DOCUMENTATION UPDATES - Version sync, timestamps, AI content generation',
  inputSchema: {
    files: ['CLAUDE.md', 'README.md'],  // Specific files or null = all
    version_bump: 'minor',               // major|minor|patch|null
    update_content: true,                // AI-generate updates
    check_links: true,                   // Validate links
    sync_related: true,                  // Update related docs
    auto_commit: true                    // Commit via auto_git_commit
  }
}
```

### Tool 2: `get_doc_status`
```javascript
{
  name: 'get_doc_status',
  description: 'Get documentation status - versions, last updated, broken links',
  inputSchema: {
    files: null,              // null = all docs
    check_outdated: true,     // Find outdated docs
    check_links: true         // Check all links
  }
}
```

### Tool 3: `find_doc_files`
```javascript
{
  name: 'find_doc_files',
  description: 'Find all documentation files in project',
  inputSchema: {
    base_dir: '/home/wil',
    patterns: ['*.md', 'README*', '*_GUIDE.md']
  }
}
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE IF NOT EXISTS docs_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    old_version TEXT,
    new_version TEXT,
    changes_made TEXT,           -- JSON array
    sections_updated TEXT,       -- JSON array
    links_checked INTEGER DEFAULT 0,
    broken_links TEXT,           -- JSON array
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT DEFAULT 'coordinator-agent',
    commit_hash TEXT,            -- Link to git_commits
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_docs_file ON docs_updates(file_path);
CREATE INDEX IF NOT EXISTS idx_docs_version ON docs_updates(new_version);
CREATE INDEX IF NOT EXISTS idx_docs_date ON docs_updates(updated_at);
```

---

## 💡 Smart Features

### 1. Version Number Detection
**Patterns to Find:**
```markdown
# Version: 7.2
# v7.2
Version: 7.2 | Updated: Oct 20
Last Updated: October 20, 2025 (v7.2)
```

### 2. Timestamp Patterns
```markdown
Updated: Oct 20, 2025
Date: October 20, 2025 19:00 UTC
Last Updated: 2025-10-20
Modified: Mon Oct 20 19:00:00 UTC 2025
```

### 3. AI Content Generation
**Example:**
```markdown
Recent Changes (Auto-Generated):
- Added git automation system (Oct 20, 18:30 UTC)
- Implemented auto_git_commit MCP tool
- Created git-helpers.js with 9 functions
- 30x faster commits with AI messages
```

### 4. Cross-Reference Sync
**Example:**
- CLAUDE.md line 428: "Tools: 19 tools"
- README.md should say: "19 MCP tools available"
- If one updates, sync the other

---

## 🎯 Use Cases

### Use Case 1: Version Bump After Feature
```javascript
// After implementing new feature
auto_update_docs({
  files: null,                 // All docs
  version_bump: 'minor',       // 7.2 → 7.3
  update_content: true,        // Add to changelog
  auto_commit: true            // Commit changes
})

// Results:
// - CLAUDE.md: Version 7.2 → 7.3
// - README.md: Version synced
// - Changelog: "v7.3 - Added documentation automation"
// - Timestamps: Updated to current
// - Git commit: "docs: Update to v7.3 - documentation automation"
```

### Use Case 2: Fix Broken Links
```javascript
auto_update_docs({
  files: ['CLAUDE.md'],
  check_links: true,
  auto_commit: false           // Just report, don't commit
})

// Results:
// - Checked 47 links
// - Found 3 broken links:
//   - Line 234: ~/old-file.md (404)
//   - Line 456: http://example.com/dead (timeout)
//   - Line 789: ../missing.md (not found)
```

### Use Case 3: Update Status Section
```javascript
auto_update_docs({
  files: ['CLAUDE.md'],
  sections: ['STATUS', 'MCP SERVERS'],
  update_content: true,
  auto_commit: true
})

// Results:
// - STATUS section updated with current service status
// - MCP SERVERS section updated with tool count
// - Timestamp updated
// - Git commit: "docs: Update status sections"
```

---

## 📊 Expected Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Time to update docs** | 10-15 min | 30 sec | **30x faster** |
| **Version consistency** | Manual (errors) | Automatic | **100% consistent** |
| **Broken links** | Unknown | Detected | **0 broken links** |
| **Changelog** | Manual | AI-generated | **Always current** |
| **Doc updates missed** | 30% | 0% | **100% coverage** |

---

## 🔒 Safety Features

1. **Backup Before Update**
   - Create `.backup` file before modifying
   - Rollback on error

2. **Validation**
   - Validate markdown syntax before commit
   - Check links before marking as fixed
   - Verify version format

3. **Git Integration**
   - All doc updates committed via auto_git_commit
   - Conventional commit messages
   - Full audit trail

4. **Selective Updates**
   - Can update specific files only
   - Can update specific sections only
   - Non-destructive by default

---

## 🚀 Implementation Steps

1. ✅ **Design Complete** (this document)
2. ⏳ **Implement docs-helpers.js** (~400 lines)
3. ⏳ **Enhance coordinator-agent.js** (+250 lines, 3 methods)
4. ⏳ **Update MCP server** (+100 lines, 3 new tools)
5. ⏳ **Create database table** (docs_updates schema)
6. ⏳ **Test with CLAUDE.md** (update to v7.3)
7. ⏳ **Create documentation** (implementation report)

---

**Made by Insa Automation Corp for OpSec**
**Design Date:** October 20, 2025 19:00 UTC
**Version:** 1.0 - Initial Design
