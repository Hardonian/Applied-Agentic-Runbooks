# Release Process

This document outlines the process for releasing new versions of Agent Factory.

---

## Release Checklist

### Pre-Release

- [ ] `make verify-release` passes
- [ ] Full non-integration test suite passes
- [ ] Live API E2E suite passes
- [ ] Package build and `twine check` pass
- [ ] Authenticated signup, agent, and workflow product path passes
- [ ] Dependency audit passes and a CycloneDX SBOM is attached
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in pyproject.toml
- [ ] Version bumped in __init__.py
- [ ] Security audit completed
- [ ] Performance tested
- [ ] Breaking changes documented
- [ ] Migration guide updated (if needed)

### Release Steps

1. **Update Version**
   ```bash
   # Update pyproject.toml
   version = "0.2.0"
   
   # Update agent_factory/__init__.py
   __version__ = "0.2.0"
   ```

2. **Update CHANGELOG.md**
   - Move items from `[Unreleased]` to new version section
   - Add release date
   - Document all changes

3. **Create Release Branch**
   ```bash
   git checkout -b release/0.2.0
   git add .
   git commit -m "chore: Release 0.2.0"
   git push origin release/0.2.0
   ```

4. **Create Pull Request**
   - Open PR from release branch to main
   - Get review and approval
   - Merge to main

5. **Tag Release**
   ```bash
   git checkout main
   git pull origin main
   git tag -a v0.2.0 -m "Release 0.2.0"
   git push origin v0.2.0
   ```

6. **Let the Release workflow close the release**
   - The `Release` workflow is triggered by the pushed `v*` tag.
   - It verifies the tag, package metadata, and changelog alignment.
   - It runs the non-integration suite, builds both distributions, installs the
     wheel in an isolated environment, and runs the live API E2E suite against
     that built artifact, including signup and protected agent/workflow flows.
   - It audits installed release dependencies and attaches a CycloneDX SBOM.
   - Only after all gates pass does it create the GitHub release and attach the
     source and wheel distributions with generated release notes.

7. **Publish to PyPI** (if applicable)
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

### Post-Release

- [ ] Monitor for issues
- [ ] Respond to feedback
- [ ] Update documentation if needed
- [ ] Announce release to community
- [ ] Plan next release

---

## Release Notes Template

```markdown
## Release 0.2.0 - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing features

### Fixed
- Bug fixes

### Deprecated
- Features marked for removal

### Removed
- Removed features

### Security
- Security improvements
```

---

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes, backward compatible

---

## Release Schedule

- **Major releases:** As needed (breaking changes)
- **Minor releases:** Monthly (new features)
- **Patch releases:** As needed (bug fixes)

---

## Emergency Releases

For critical security fixes:

1. Create hotfix branch from main
2. Fix the issue
3. Test thoroughly
4. Release immediately
5. Follow up with proper release process

---

## Questions?

Contact maintainers or open an issue.
