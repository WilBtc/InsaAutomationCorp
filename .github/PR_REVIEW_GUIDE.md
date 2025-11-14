# Pull Request Review Guide

## For PR Authors

### Creating a Good PR
1. **Keep it small** - Aim for < 500 lines changed
2. **One concern per PR** - Don't mix features/bugs/refactoring
3. **Write clear description** - Explain what and why
4. **Complete checklist** - All items must be checked
5. **Add tests** - Code coverage should not decrease
6. **Update documentation** - Keep docs in sync

### Before Submitting
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] No merge conflicts
- [ ] Checklist fully completed
- [ ] Clear title and description

## For Reviewers

### What to Check
1. **Functionality** - Does it do what it claims?
2. **Security** - Any vulnerabilities introduced?
3. **Performance** - Any performance regressions?
4. **Tests** - Adequate test coverage?
5. **Documentation** - Is it documented?
6. **Code Quality** - Readable, maintainable code?

### Review Timeline
- **Small PR (< 100 lines)**: 24 hours
- **Medium PR (100-500 lines)**: 48 hours
- **Large PR (> 500 lines)**: 72 hours
- **Critical/Security**: 4 hours

### Approval Criteria
- ✅ All checklist items completed
- ✅ All CI checks passing
- ✅ No unresolved comments
- ✅ Adequate test coverage
- ✅ Documentation updated (if needed)
- ✅ No security issues detected

## Automated Checks

Our PR workflow includes:
1. **Danger.js** - AI-powered review comments
2. **CodeQL** - Security vulnerability scanning
3. **Secret Scanning** - Credential detection
4. **Size Check** - PR size warnings
5. **Checklist Verification** - Ensure template compliance

## Review Best Practices

### For Authors
- **Respond promptly** to reviewer comments
- **Explain your reasoning** if you disagree
- **Update the PR** based on feedback
- **Mark conversations resolved** when addressed

### For Reviewers
- **Be constructive** - Focus on improving the code
- **Be specific** - Point to exact lines/issues
- **Be timely** - Review within the timeline above
- **Be thorough** - Check all aspects (security, performance, tests)

## PR Labels

- `size/S` - Small PR (< 200 lines)
- `size/M` - Medium PR (200-500 lines)
- `size/L` - Large PR (500-1000 lines)
- `size/XL` - Extra large PR (> 1000 lines)
- `stale` - No activity for 30 days
- `work-in-progress` - Not ready for review
- `blocked` - Waiting on dependencies
- `critical` - High priority review needed

## Common Issues

### Missing Template
If you see "Missing Checklist" warning:
1. Close the PR
2. Recreate using the template
3. Complete all checklist items

### Large PR Warning
If your PR is too large:
1. Consider splitting into multiple PRs
2. Group related changes together
3. Submit smaller, focused PRs

### Security Concerns
If security-sensitive files are modified:
1. Extra scrutiny required
2. Consider security testing
3. Update security documentation

## Escalation

If you need urgent review or have concerns:
1. Tag @WilBtc in comments
2. Add `critical` label
3. Explain the urgency

---
📋 Part of INSA Automation Corp Quality Standards
🤖 Automated PR Review System
