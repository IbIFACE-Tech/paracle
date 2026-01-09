# Git Workflow Policy

## Branch Strategy

### Main Branches
- `main` - Production-ready code
- `develop` - Integration branch
- `staging` - Pre-production testing

### Feature Branches
- Pattern: `feature/<ticket-id>-<description>`
- Example: `feature/PROJ-123-user-authentication`
- Created from: `develop`
- Merged to: `develop`

### Bugfix Branches
- Pattern: `bugfix/<ticket-id>-<description>`
- Example: `bugfix/PROJ-456-login-error`
- Created from: `develop` or `main` (hotfix)
- Merged to: `develop` and `main` (if hotfix)

### Release Branches
- Pattern: `release/v<version>`
- Example: `release/v1.2.0`
- Created from: `develop`
- Merged to: `main` and `develop`

## Commit Convention

Follow Conventional Commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(auth): add JWT authentication

Implement JWT-based authentication with refresh tokens.
Includes rate limiting and token rotation.

Closes PROJ-123
```

```
fix(api): resolve database connection leak

Database connections were not being properly closed
in error conditions.

Fixes PROJ-456
```

## Pull Request Process

### 1. Create PR
- Use PR template
- Link to ticket/issue
- Add description
- Mark as draft if WIP

### 2. Code Review
- Minimum 2 approvals required
- Address all comments
- Pass all CI checks

### 3. Testing
- All tests pass
- Coverage maintained/improved
- Manual testing completed

### 4. Merge
- Use "Squash and merge"
- Delete branch after merge
- Update ticket status

## Release Process

1. Create release branch from `develop`
2. Bump version number
3. Update CHANGELOG.md
4. Test in staging
5. Merge to `main`
6. Tag release
7. Merge back to `develop`
8. Deploy to production

## Versioning

Follow Semantic Versioning (SemVer):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

Example: `v1.2.3`

## Protected Branches

### main
- Require PR reviews (2)
- Require status checks
- No force push
- No deletions

### develop
- Require PR reviews (1)
- Require status checks
- No force push

## Git Hooks

### Pre-commit
- Run code formatters
- Run linters
- Check for secrets

### Pre-push
- Run unit tests
- Check coverage

## Best Practices

- Commit early and often
- Write meaningful commit messages
- Keep commits focused and atomic
- Rebase feature branches regularly
- Never commit secrets
- Use `.gitignore` properly
