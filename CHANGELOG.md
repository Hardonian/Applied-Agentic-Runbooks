# Changelog

**Founder, CEO & Operator:** Scott Hardie

All notable changes to Agent Factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-12

### Added
- Comprehensive documentation rewrite for human-friendly onboarding
- USE_CASES.md with 10 concrete real-world examples
- PRODUCT_OVERVIEW.md for product positioning
- SAAS_STARTER.md guide for SaaS builders
- COMMUNITY.md for community guidelines
- ROADMAP.md for future development
- MONETIZATION.md for monetization strategies
- MAINTENANCE.md for long-term maintenance
- API_REFERENCE.md improvements
- Developer experience enhancements
- Enterprise SSO, webhooks, compliance controls, and referral APIs
- Runtime scheduling and orchestration execution
- Release verification and tag-driven release automation
- Authenticated signup, agent, and workflow product-path E2E coverage
- Dependency audit and CycloneDX SBOM release artifacts

### Changed
- README.md completely rewritten for better onboarding
- Documentation humanized across all docs
- Improved error messages and developer feedback
- Enhanced API documentation

### Fixed
- Import consistency across codebase
- Documentation links and references
- Example code snippets
- Consistent package, API, health, and CLI version reporting
- Pinned bcrypt below 5.0 until passlib has a compatible password-hashing integration

## [0.1.0] - 2024-01-XX

### Added
- Core Agent, Tool, and Workflow primitives
- Blueprint system for reusable configurations
- REST API with FastAPI
- CLI interface with Typer
- Python SDK
- Local and remote registries
- Runtime engine for execution
- Telemetry and observability
- Security and authentication
- Billing and usage tracking
- Multi-tenant support
- Knowledge pack system
- Notebook converter
- Evaluation framework
- Marketplace integration
- Education-focused blueprints

### Changed
- Initial release

---

## Release Notes Template

### Version X.Y.Z - YYYY-MM-DD

#### Added
- New features and functionality

#### Changed
- Changes to existing functionality

#### Deprecated
- Features that will be removed in future versions

#### Removed
- Features removed in this version

#### Fixed
- Bug fixes

#### Security
- Security improvements

---

## How to Update This Changelog

1. Add new entries under `[Unreleased]`
2. When releasing, move `[Unreleased]` entries to a new version section
3. Update the version date
4. Follow semantic versioning (MAJOR.MINOR.PATCH)
