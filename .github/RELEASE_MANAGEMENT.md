# Release Management Guide

## Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features (backward compatible)
- **PATCH** (0.0.X): Bug fixes (backward compatible)

## Conventional Commits

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types
- **feat**: New feature → MINOR version bump
- **fix**: Bug fix → PATCH version bump
- **docs**: Documentation only → PATCH version bump
- **style**: Code style changes (formatting) → No version bump
- **refactor**: Code refactoring → No version bump
- **perf**: Performance improvement → PATCH version bump
- **test**: Test changes → No version bump
- **chore**: Build/tooling changes → No version bump
- **ci**: CI/CD changes → No version bump
- **build**: Build system changes → No version bump
- **revert**: Revert previous commit → PATCH version bump

### Breaking Changes
Add `BREAKING CHANGE:` in footer → MAJOR version bump

### Examples

**New Feature (MINOR)**:
```
feat(agents): Add autonomous merge conflict resolution

Implements AI-powered conflict resolution for GitHub PRs using
rebase + simple strategies for 60-70% auto-resolution.
```

**Bug Fix (PATCH)**:
```
fix(github-ci-fixer): Prevent duplicate workflow runs

Add debounce logic to prevent multiple simultaneous runs on
rapid pushes.
```

**Breaking Change (MAJOR)**:
```
feat(mcp-servers)!: Upgrade to MCP SDK 2.0

BREAKING CHANGE: MCP SDK 1.x servers no longer supported.
All servers must migrate to SDK 2.0 API.
```

## Release Process

### Automated (Recommended)
1. Merge PR to `main` branch
2. Release workflow runs automatically
3. Version calculated from commits
4. Changelog generated
5. Git tag created
6. GitHub Release published

### Manual
1. Go to Actions → Release Management
2. Click "Run workflow"
3. Select release type: patch/minor/major/auto
4. Click "Run workflow"

## Version File

Current version stored in `VERSION` file at repository root.

## Changelog

Auto-generated from commits and saved in GitHub Releases.

## Release Notes

Generated automatically with sections:
- ✨ Features
- 🐛 Bug Fixes
- 📝 Documentation
- 🔧 Chores

## Checking Current Version

```bash
cat VERSION
# or
git describe --tags --abbrev=0
```

## Creating Pre-releases

Use branch naming:
- `beta`: Pre-release versions (1.0.0-beta.1)
- `alpha`: Alpha versions (1.0.0-alpha.1)
- `rc`: Release candidates (1.0.0-rc.1)

## Best Practices

1. **Always** use conventional commits
2. **Never** manually edit VERSION file
3. **Test** before merging to main
4. **Document** breaking changes in commit footer
5. **Keep** commits focused and atomic

## Examples of Good Commits

### Feature Addition
```
feat(autonomous-agents): Add GitHub merge conflict auto-resolution

Implements intelligent merge conflict resolution using rebase strategy
for simple conflicts (non-overlapping line changes). Achieves 60-70%
auto-resolution rate for typical development scenarios.

Key features:
- Rebase strategy for clean history
- Simple conflict detection
- Automatic resolution for non-overlapping changes
- Manual escalation for complex conflicts
```

### Bug Fix
```
fix(azure-monitor): Prevent memory leak in health check loop

Fixed issue where health check connections weren't properly closed,
causing gradual memory increase over 24+ hours of operation.

Closes #42
```

### Documentation
```
docs(mcp-servers): Add troubleshooting guide for common MCP SDK issues

Added comprehensive troubleshooting section covering:
- Connection timeout errors
- Authentication failures
- Tool invocation issues
- Performance optimization tips
```

### Performance Improvement
```
perf(orchestrator): Reduce database query time by 80%

Optimized task scanning by adding compound index on
(status, created_at) columns. Reduced average query
time from 500ms to 100ms under load.
```

### Breaking Change
```
feat(host-config-agent)!: Migrate to MCP SDK 2.0 protocol

BREAKING CHANGE: Host Config Agent now requires MCP SDK 2.0+.
Clients using SDK 1.x must upgrade before deployment.

Migration guide: docs/MIGRATION_SDK_2.0.md
```

## Release Workflow Details

### Automatic Version Calculation

The release workflow automatically calculates the next version based on:

1. **Current version** from `VERSION` file
2. **Commit history** since last release
3. **Release type** (manual trigger only):
   - `auto`: Analyzes commits (default)
   - `patch`: Force patch bump (0.0.X)
   - `minor`: Force minor bump (0.X.0)
   - `major`: Force major bump (X.0.0)

### Changelog Generation

The workflow groups commits by type:
- ✨ **Features**: All `feat:` commits
- 🐛 **Bug Fixes**: All `fix:` commits
- 📝 **Documentation**: All `docs:` commits
- 🔧 **Chores**: All `chore:` commits

Example output:
```markdown
## What's Changed

### ✨ Features
- feat(agents): Add autonomous merge conflict resolution (a1b2c3d)
- feat(mcp): Add new GitHub integration tools (e4f5g6h)

### 🐛 Bug Fixes
- fix(azure): Prevent connection timeout in health checks (i7j8k9l)

### 📝 Documentation
- docs(release): Add comprehensive release management guide (m0n1o2p)

**Full Changelog**: https://github.com/WilBtc/InsaAutomationCorp/compare/v1.0.0...v1.1.0
```

## Commit Message Linting

All PRs are automatically checked for conventional commit format:

### Rules
- Type must be one of: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert
- Type must be lowercase
- Subject is required
- Subject must be 10-100 characters
- Header must not exceed 100 characters

### Common Mistakes

❌ **Bad**: `Added new feature`
✅ **Good**: `feat(agents): Add autonomous merge conflict resolution`

❌ **Bad**: `fix bug`
✅ **Good**: `fix(orchestrator): Prevent race condition in task scheduling`

❌ **Bad**: `FEAT: NEW FEATURE`
✅ **Good**: `feat(crm): Add lead scoring algorithm`

## Troubleshooting

### Release Workflow Fails

**Problem**: Release workflow fails with "No commits found"
**Solution**: Ensure at least one commit exists since last tag

**Problem**: Release workflow fails with "Permission denied"
**Solution**: Check GitHub Actions has write permissions for contents

**Problem**: VERSION file not updated
**Solution**: Verify workflow has git write permissions and proper authentication

### Commit Lint Fails

**Problem**: "Subject too short"
**Solution**: Ensure subject is at least 10 characters

**Problem**: "Invalid type"
**Solution**: Use one of the allowed types (feat, fix, docs, etc.)

**Problem**: "Header too long"
**Solution**: Keep entire commit message header under 100 characters

## Integration with INSA Systems

### Autonomous Orchestrator
The orchestrator will automatically detect new releases and can:
- Update deployment configurations
- Notify teams of breaking changes
- Schedule upgrade windows

### Host Config Agent
Release information is tracked in the host config database:
- Version deployments
- Rollback points
- Compatibility matrix

### MCP Servers
All MCP servers follow semantic versioning:
- Breaking changes require major version bump
- New tools require minor version bump
- Bug fixes require patch version bump

## Support

For questions or issues with release management:
- GitHub Issues: https://github.com/WilBtc/InsaAutomationCorp/issues
- Email: w.aroca@insaing.com
- Documentation: .github/RELEASE_MANAGEMENT.md

## License

Made by INSA Automation Corp
