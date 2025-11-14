# Branch Protection Policy

**Version**: 1.0.0 | **Last Updated**: November 14, 2025 | **Managed by**: GitHub CI Fixer Agent

This document describes the branch protection rules enforced on the InsaAutomationCorp repository. These rules are automatically enforced and monitored by the GitHub CI Fixer agent.

## Overview

Branch protection rules prevent:
- Force pushes to critical branches
- Accidental deletions
- Merging code without proper review
- Merging code that fails automated checks
- History rewrites on main branch

## Protected Branches

### Main Branch (`main`)

The primary release branch with the strictest protection rules.

#### Protection Rules

| Rule | Setting | Purpose |
|------|---------|---------|
| **Require pull request reviews** | 1 approval | At least one code review before merge |
| **Require code owner review** | Enabled | Code owners must approve changes |
| **Dismiss stale reviews** | Yes | New commits require fresh review |
| **Require status checks** | Strict | All CI/CD checks must pass AND be up-to-date |
| **Required status checks** | CodeQL, Secret Scanning, Commit Lint, PR Review | Mandatory checks for all PRs |
| **Enforce for admins** | Yes | Even repository admins must follow rules |
| **Linear history** | Required | Force pushes and history rewrites blocked |
| **Allow force pushes** | No | Prevents emergency overwrites |
| **Allow deletions** | No | Prevents accidental branch removal |

#### Required Status Checks

All the following must pass before a PR can merge to main:

1. **CodeQL** (Security scanning)
   - GitHub's static analysis for security vulnerabilities
   - Scans: JavaScript, TypeScript, Python, Java, C++, C#, Go, Ruby
   - Fails on: Hardcoded credentials, SQL injection, XSS, unsafe deserialization

2. **Secret Scanning** (Credential detection)
   - Detects exposed API keys, tokens, passwords
   - Fails on: GitHub tokens, AWS keys, private keys, database credentials
   - Pattern-based detection + machine learning

3. **Commit Lint** (Conventional commits)
   - Enforces commit message format
   - Fails on: Non-standard messages, missing scope/type
   - Example valid format: `feat(ci-fixer): Add branch protection automation`

4. **PR Review Checks** (Automated code review)
   - Uses Danger.js for code quality analysis
   - Fails on: Large unreviewed PRs, missing test coverage, security issues
   - Customizable rules in `Dangerfile`

#### Example Workflow

```
1. Developer creates feature branch from main
2. Developer pushes commits
3. GitHub Actions runs CodeQL, Secret Scanning
4. Developer opens PR
5. PR Review system (Danger.js) analyzes code
6. Required checks all pass ✅
7. Code owner reviews and approves ✅
8. Developer clicks "Squash and merge"
9. PR merges to main
10. New commit triggers deployment workflow
```

#### Example Violation

```
❌ Attempting to merge PR #42 to main
   - CodeQL check: FAILED (SQL injection detected)
   - Secret Scanning: ✅ PASSED
   - Commit Lint: FAILED (Invalid message format)
   - PR Review: ✅ PASSED

Cannot merge: Fix security issues and commit message before retrying
```

### Develop Branch (`develop`)

Secondary branch for integration and pre-release testing.

#### Protection Rules

| Rule | Setting | Purpose |
|------|---------|---------|
| **Require pull request reviews** | 1 approval | One review required |
| **Code owner review** | Disabled | Flexibility for development phase |
| **Status checks** | Strict | All checks must pass and be current |
| **Enforce for admins** | Disabled | Faster iteration in dev |
| **Linear history** | Not required | Development flexibility |
| **Allow force pushes** | No | Prevent accidental data loss |
| **Allow deletions** | No | Prevent accidental removal |

#### When to Use

- Integration testing of multiple features
- Pre-release validation
- Staging environment deployments
- Cross-team review before main merge

### Release Branches (Pattern: `release/v*.*.*`)

Branches following semantic versioning pattern (e.g., `release/v1.2.3`).

#### Protection Rules

| Rule | Setting |
|------|---------|
| **Pattern** | `^release/v\d+\.\d+\.\d+$` |
| **PR Reviews** | 1 approval required |
| **Code Owner Review** | Yes |
| **Status Checks** | All (CodeQL, Secret Scanning, Commit Lint, Tests) |
| **Enforce for Admins** | Yes |
| **Force Pushes** | Disabled |
| **Deletions** | Disabled |

## Enforcement & Monitoring

### Automated Enforcement

The GitHub CI Fixer agent automatically:

1. **Daily Compliance Checks** (2 AM UTC)
   - Verifies all protected branches are properly configured
   - Generates compliance reports
   - Creates issues if violations detected

2. **Push-Time Validation** (On every push)
   - Checks status checks before allowing merge
   - Verifies review requirements
   - Prevents policy violations

3. **Violation Reporting**
   - Creates automated GitHub issues for violations
   - Tags with `security` and `branch-protection` labels
   - Includes remediation steps

### Monitoring Workflow

See `.github/workflows/branch-protection.yml` for implementation details.

**Trigger Events:**
- Daily at 2 AM UTC (compliance check)
- On push to main/develop
- On manual trigger (workflow_dispatch)
- When policy file is updated

**Enforcement Checks:**
1. Branch protection exists
2. Required status checks configured
3. Review requirements set
4. Admin enforcement enabled
5. Force push/deletion disabled

## Common Scenarios

### Scenario 1: "CodeQL Check Failed"

**Problem**: You're trying to merge a PR but CodeQL scan found a security issue.

**Solution**:
```bash
# 1. Pull latest changes
git pull origin main

# 2. Review CodeQL alert details
# Go to: https://github.com/WilBtc/InsaAutomationCorp/security/code-scanning

# 3. Fix the security issue in your code
# Example: Parameterize SQL queries, validate user input

# 4. Push the fix
git push origin feature/your-feature

# 5. Re-run CodeQL (automatic)
# Wait for workflow to complete

# 6. When all checks pass, merge PR
```

**Common CodeQL Issues:**
- SQL injection: Use parameterized queries
- XSS: Sanitize user input
- Hardcoded credentials: Use environment variables
- Unsafe deserialization: Validate data types

### Scenario 2: "Secret Scanning Detected Credential"

**Problem**: You accidentally committed an API key or token.

**Solution**:
```bash
# 1. Immediately revoke the credential
# GitHub: https://github.com/settings/tokens
# AWS: https://console.aws.amazon.com/iam/

# 2. Remove from commit history
git rebase -i HEAD~3  # Replace last 3 commits
# Remove the line with the secret

# 3. Force push to your feature branch (NOT main!)
git push origin feature/your-feature --force-with-lease

# 4. Verify Secret Scanning passes
# Wait for workflow to complete

# 5. Merge PR
```

**Never expose:**
- GitHub personal access tokens
- AWS/Azure credentials
- Database passwords
- SSH private keys
- API keys for any service

### Scenario 3: "PR Review Check Failed - Large PR"

**Problem**: Your PR has 1,500 lines of changes and Danger.js rejected it.

**Solution**:
```bash
# 1. Split into smaller PRs (1 concern each)
# Good PR: "feat: Add user authentication" (200 lines)
# Bad PR: "feat: Add auth + refactor database + new UI" (1500 lines)

# 2. Each PR should:
#   - Have one clear purpose
#   - Include tests
#   - Include documentation
#   - Be under 500 lines if possible

# 3. Link related PRs in description
# Example: "This PR is part of feature X. Related: #41, #42"

# 4. Resubmit smaller PRs
```

**PR Size Guidelines:**
- Small (<200 lines): ✅ Ideal
- Medium (200-500 lines): ⚠️ OK
- Large (500-1000 lines): ⚠️ Needs justification
- XL (>1000 lines): ❌ Must split

### Scenario 4: "Code Owner Review Required"

**Problem**: You need a code owner's approval but they're unavailable.

**Solution**:
```bash
# 1. Check CODEOWNERS file
cat .github/CODEOWNERS

# 2. Identify code owner
# For most files: @WilBtc

# 3. Contact the code owner
# Email: w.aroca@insaing.com
# GitHub: @WilBtc

# 4. Request review on PR (GitHub UI or mention in comment)
# Click "Request a review" button

# 5. Code owner approves or requests changes

# 6. Make any requested changes

# 7. After approval, PR auto-merges if other checks pass
```

## Policies by File Type

### Python Files (`.py`)

**Requirement**: All Python changes require CodeQL scan
**Process**:
1. Write code following Python standards
2. Add docstrings to functions/classes
3. Include tests in `tests/` directory
4. Push to feature branch
5. CodeQL scans automatically
6. Fix any issues found
7. Merge when checks pass

### Workflow Files (`.github/workflows/*.yml`)

**Requirement**: Security review + CodeQL + Secret Scanning
**Process**:
1. Test locally with `act` tool
2. Ensure no hardcoded credentials
3. Review workflow syntax
4. Push to feature branch
5. All automated checks must pass
6. Merge when approved

### Configuration Files (`*.yml`, `*.json`, `.env.*`)

**Requirement**: No credentials + YAML/JSON validation
**Process**:
1. Remove any sensitive data
2. Use `${{ secrets.VARIABLE_NAME }}` for runtime values
3. Validate syntax (YAML linter, JSON schema)
4. Document all configuration options
5. Merge when checks pass

### Documentation Files (`.md`)

**Requirement**: CodeQL + basic review
**Process**:
1. Follow Markdown best practices
2. Include examples
3. Update table of contents if needed
4. Check links are valid
5. Merge when approved

## Troubleshooting

### "Branch Protection Not Found"

**Error**: GitHub reports branch protection doesn't exist but you configured it.

**Fix**:
1. Go to Settings → Branches
2. Find the branch name (case-sensitive)
3. Click "Add rule" if missing
4. Configure according to `.github/branch-protection.yml`
5. Save changes
6. Wait 5 minutes for webhook delivery

### "Required Status Checks Timeout"

**Error**: GitHub shows "required status check is expected but hasn't completed yet"

**Fix**:
1. Check workflow status: Actions tab in GitHub
2. If workflow is running: Wait for completion
3. If workflow is stuck:
   - Cancel the workflow
   - Push an empty commit: `git commit --allow-empty -m "retry"`
   - Workflow reruns automatically
4. Check system status: https://www.githubstatus.com/

### "Can't Merge - Reviews Dismissed"

**Error**: "Some checks were not successful" and "stale review warning"

**Fix**:
1. A new commit was pushed after code owner review
2. Code owner review is now "stale"
3. Solution: Ask code owner to review again
4. Or modify only test/doc files (won't dismiss review)

### "Admin Can't Override"

**Error**: "You are an administrator, but branch protection rules apply to admins"

**Fix**:
This is working as intended (security feature). To merge:
1. Create a proper PR
2. Get required approvals
3. Pass all status checks
4. Merge through GitHub UI

If truly emergency: Contact repository owner

## Violation Response

### Automatic Issue Creation

When violations are detected:

1. Workflow runs daily at 2 AM UTC
2. Checks all protected branches
3. Compares to `.github/branch-protection.yml`
4. If mismatch found:
   - Creates GitHub issue with label `branch-protection`
   - Includes violation details
   - Provides remediation steps

### How to Resolve

1. Read the automated issue
2. Note what's misconfigured
3. Go to Settings → Branches
4. Click "Edit" on protected branch
5. Adjust settings to match policy file
6. Click "Save changes"
7. Wait for next compliance check (daily)
8. Issue auto-closes when resolved

## Policy Changes

### Updating Protection Rules

To change branch protection rules:

1. **Edit `.github/branch-protection.yml`**
   ```yaml
   main:
     required_pull_request_reviews:
       required_approving_review_count: 2  # Changed from 1
   ```

2. **Push to feature branch**
   ```bash
   git checkout -b feature/stronger-protection
   git add .github/branch-protection.yml
   git commit -m "feat: Increase required reviews to 2"
   git push origin feature/stronger-protection
   ```

3. **Create PR and get approval**
   - All checks must pass
   - Code owner review required
   - Merge when approved

4. **Manually update GitHub UI**
   - Go to Settings → Branches
   - Apply the changes from the policy file
   - Save changes

5. **Verify compliance**
   - Next daily check (2 AM UTC) validates changes
   - Or manually trigger workflow

## Support & Escalation

### Questions?

Contact: **Wil Aroca** (w.aroca@insaing.com)

### Need Emergency Override?

Only repository owner (@WilBtc) can temporarily disable rules:

1. Go to Settings → Branches
2. Uncheck protection rules
3. Make the merge
4. **Immediately** re-enable protection
5. Document reason in GitHub issue

### Report Issues

1. Check existing issues: https://github.com/WilBtc/InsaAutomationCorp/issues
2. If new issue:
   - Title: "Branch Protection: [Issue]"
   - Label: `branch-protection`
   - Include error message and reproduction steps

## Related Documentation

- **Workflow Implementation**: `.github/workflows/branch-protection.yml`
- **Protection Policy File**: `.github/branch-protection.yml`
- **PR Review System**: `.github/PR_REVIEW_GUIDE.md`
- **CI Fixer Agent**: `automation/agents/github-ci-fixer/README.md`
- **CODEOWNERS**: `.github/CODEOWNERS`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-14 | Initial release - Main/Develop/Release branch protection |

---

**Last Updated**: November 14, 2025
**Managed by**: GitHub CI Fixer Agent
**Source**: `.github/branch-protection.yml`
**Workflow**: `.github/workflows/branch-protection.yml`
