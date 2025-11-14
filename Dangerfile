// INSA Automation Corp - Automated PR Review Rules

import { danger, warn, fail, message } from 'danger';

const pr = danger.github.pr;
const modified = danger.git.modified_files;
const created = danger.git.created_files;
const deleted = danger.git.deleted_files;
const allFiles = [...modified, ...created];

// Check PR size
const bigPRThreshold = 500;
const totalChanges = pr.additions + pr.deletions;
if (totalChanges > bigPRThreshold) {
  warn(`⚠️ This PR is quite large (${totalChanges} lines changed). Consider splitting into smaller PRs.`);
}

// Check for WIP or Draft
if (pr.title.includes('WIP') || pr.title.includes('[WIP]') || pr.draft) {
  warn('🚧 This PR is marked as Work in Progress. Not ready for merge.');
}

// Check for description
if (pr.body.length < 50) {
  fail('❌ Please add a detailed PR description (minimum 50 characters).');
}

// Check for tests
const hasTestChanges = allFiles.some(file => file.includes('test') || file.includes('spec'));
const hasCodeChanges = allFiles.some(file => file.endsWith('.py') && !file.includes('test'));
if (hasCodeChanges && !hasTestChanges) {
  warn('⚠️ Code changes detected but no test files modified. Consider adding tests.');
}

// Check for security-sensitive changes
const securityFiles = allFiles.filter(file =>
  file.includes('password') ||
  file.includes('secret') ||
  file.includes('credential') ||
  file.includes('.env') ||
  file.includes('auth')
);
if (securityFiles.length > 0) {
  warn(`🔒 Security-sensitive files modified: ${securityFiles.join(', ')}. Extra review required!`);
}

// Check for dependency changes
const dependencyFiles = allFiles.filter(file =>
  file.includes('requirements.txt') ||
  file.includes('package.json') ||
  file.includes('Pipfile')
);
if (dependencyFiles.length > 0) {
  message(`📦 Dependencies updated. Security scan will run automatically.`);
}

// Check for large files
allFiles.forEach(file => {
  const fileSize = danger.github.utils.fileContents(file).length;
  if (fileSize > 500000) { // 500KB
    warn(`⚠️ Large file detected: ${file} (${(fileSize/1024).toFixed(2)} KB)`);
  }
});

// Encourage small PRs
if (totalChanges < 100) {
  message('✅ Nice small PR! Easy to review.');
}

// Check for documentation updates
const hasDocsChanges = allFiles.some(file => file.endsWith('.md'));
const hasSignificantCodeChanges = totalChanges > 100 && hasCodeChanges;
if (hasSignificantCodeChanges && !hasDocsChanges) {
  warn('📝 Significant code changes without documentation updates. Consider updating docs.');
}
