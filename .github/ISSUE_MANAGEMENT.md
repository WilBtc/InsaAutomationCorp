# Issue Management Guide

## Issue Types

We use templates for 3 issue types:
1. **🐛 Bug Report** - Something is broken
2. **✨ Feature Request** - New functionality needed
3. **🔒 Security Vulnerability** - Security issues (confidential)

## Issue Lifecycle

1. **New** → Automatically labeled "needs-triage"
2. **Triaged** → Assigned, prioritized, component labeled
3. **In Progress** → Labeled "in-progress"
4. **Resolved** → Closed with resolution comment
5. **Stale** → Auto-closed after 60 days inactivity

## Labels

### Priority
- `priority:critical` - System down, security breach
- `priority:high` - Major feature broken
- `priority:medium` - Minor issue
- `priority:low` - Nice to have

### Component
- `component:github-ci-fixer`
- `component:orchestrator`
- `component:mcp-servers`
- `component:insa-crm`
- `component:azure-monitor`

### Type
- `bug` - Something broken
- `enhancement` - New feature
- `security` - Security issue
- `documentation` - Docs issue
- `type:performance` - Performance problem
- `type:dependency` - Dependency update

### Status
- `needs-triage` - Not yet reviewed
- `in-progress` - Being worked on
- `blocked` - Waiting on something
- `stale` - Inactive for 60 days
- `possible-duplicate` - May be duplicate

## Automated Triage

Our system automatically:
1. **Labels** issues based on content
2. **Assigns** to component owner
3. **Detects** possible duplicates
4. **Closes** stale issues (60+ days inactive)

## SLA Response Times

- **Critical**: 4 hours
- **High**: 24 hours
- **Medium**: 48 hours
- **Low**: 1 week

## Best Practices

1. **Search first** - Check for duplicates
2. **Use templates** - All required info
3. **Be specific** - Clear reproduction steps
4. **Stay on topic** - One issue per report
5. **Update status** - Comment on progress

## Escalation

For urgent issues:
- Email: w.aroca@insaing.com
- Tag: @WilBtc in comments
- Label: `priority:critical`

## Issue Templates

### Bug Report
Use when something is not working as expected. Includes:
- Bug description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Severity level
- Affected component

### Feature Request
Use when suggesting new functionality. Includes:
- Problem statement
- Proposed solution
- Alternatives considered
- Priority level
- Target component

### Security Vulnerability
Use for security issues. Includes:
- Vulnerability description
- CVSS severity
- Potential impact
- Reproduction steps
- Suggested fix

**Note**: For public repositories, email security issues to w.aroca@insaing.com instead of creating public issues.

## Automation Features

### Auto-Labeling
Issues are automatically labeled based on:
- **Component keywords**: "github ci", "orchestrator", "mcp", "crm", "azure", etc.
- **Priority keywords**: "critical", "high", "medium", "low"
- **Type keywords**: "performance", "dependency", "config"

### Duplicate Detection
System checks for similar issue titles and:
- Comments with links to possible duplicates
- Adds `possible-duplicate` label

### Stale Issue Cleanup
Issues with no activity for 60 days:
- Day 60: Marked as stale with reminder comment
- Day 74: Automatically closed
- Exemptions: `critical`, `security`, `blocked`, `pinned` labels

## Contributing

When creating an issue:
1. Use the appropriate template
2. Fill all required fields
3. Be as specific as possible
4. Search for duplicates first
5. Use clear, descriptive titles

When working on an issue:
1. Self-assign when starting work
2. Add `in-progress` label
3. Comment on progress regularly
4. Link related PRs
5. Close with resolution summary
