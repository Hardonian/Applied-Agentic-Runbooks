# Changelog

**Founder, CEO & Operator:** Scott Hardie

All notable changes to Agent Factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Speculative Monte Carlo Tree Search (MCTS) & Tree-of-Thoughts Engine** (`agent_factory.reasoning.mcts`): Non-myopic multi-path hypothesis search with PUCT exploration/exploitation, dynamic dead-end pruning, and state-value backpropagation.
- **Just-In-Time (JIT) Dynamic Tool Synthesizer & Autonomous Sandbox** (`agent_factory.tools.jit_synthesizer`): Autonomous code generation, AST-level zero-trust security audit, self-testing verification suite, and live toolbelt hot-swapping.
- **Speculative Model Cascade & Pareto Cost-Latency Optimizer** (`agent_factory.optimization.cascade_router`): Fast tier speculation (gpt-4o-mini/flash) delivering 90%+ cost reduction and 4x+ latency acceleration, cascading to deep reasoning tiers only when confidence fails threshold.
- **MCPWall Zero-Trust Policy Firewall & Human Gates** (`agent_factory.security.mcpwall`): Folded in from `Hardonian/mcpwall`. Enforces tool allowlists/denylists, path root containment, argument byte limits, and single-use TTL-bound SHA-256 human approval challenges for destructive operations.
- **VeriDAG Cryptographic Merkle State Engine** (`agent_factory.orchestration.veridag`): Folded in from `Hardonian/veridag`. Deterministic DAG workflow execution generating cryptographic Merkle state transition proofs for zero-trust third-party replay verification.
- **AgentPCAP Protocol Capture & Pathology Debugger** (`agent_factory.telemetry.pcap`): Folded in from `Hardonian/AgentPCAP`. Unified timeline recording A2A, Tool, and Model frames, with deterministic zero-LLM detection of retry storms, ping-pong loops, and token burning spikes.
- **TokenGoblin Velocity Governor & Settler Dual-Entry Ledger** (`agent_factory.financial.token_goblin`): Folded in from `Hardonian/TokenGoblin` and `Hardonian/Settler`. Real-time tokens/sec rolling burnrate governor and dual-entry mathematically audited credit accounts enforcing zero-leakage reconciliation.
- **Studio Command Center 2.0 Panels**: Integrated live MCTS Tree Visualizer, Speculative Model Cascade dial, MCPWall Security Gate dashboard, and AgentPCAP Timeline inspector.
- **Advanced REST Endpoints & CLI Commands**: Exposing `/api/v1/reasoning/mcts/search`, `/api/v1/optimization/cascade/execute`, `/api/v1/tools/jit/synthesize`, `/api/v1/security/mcpwall/validate`, alongside CLI commands `mcts` and `cascade`.
- **Self-Healing Autonomous Agent Execution Engine** (`agent_factory.runtime.self_healing`): Dynamic error taxonomy (Rate limits, tool crashes, schema validation errors, timeouts), reflection-driven autonomous recovery prompts, and integrated circuit breakers.
- **Enterprise AI Compliance & Certification Generator** (`agent_factory.compliance.certification`): Cryptographic SHA-256 agent instruction fingerprints, automated OWASP Top 10 for LLMs scanning, SOC 2 Type II, HIPAA, FERPA, EU AI Act audit mapping, and exportable digital seal records.
- **Visual Studio Command Center Integration**: Mounted interactive command center at `/studio`, added `/studio` discovery link to root API, and enhanced `agent-factory serve` output.
- **Multi-Agent Swarm Orchestration Endpoint**: REST API at `/api/v1/orchestration/swarm/execute` and CLI command `agent-factory swarm` supporting hierarchical supervisor, peer debate, voting consensus, and dynamic intent routing.
- **Enterprise Agent Compliance Certification API & CLI**: REST endpoint at `/api/v1/compliance/certify` and CLI command `agent-factory certify <agent_id>`.
- **Windows Console & CP1252 Terminal Resilience**: Auto-reconfigured UTF-8 stdout/stderr streams to prevent encoding exceptions on Windows hosts.
- **Automated In-Process Reality Mode Fallback**: `scripts/verify_product.py` seamlessly executes full E2E product lifecycle using in-process TestClient with test-mode Stripe bypass.

### Fixed

- Modern bcrypt/passlib compatibility via runtime patch.
- Rate-limiting flake elimination in test environment runs.
- Mypy py310 modern typing target configuration.

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

```markdown
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
```

---

## How to Update This Changelog

1. Add new entries under `[Unreleased]`
2. When releasing, move `[Unreleased]` entries to a new version section
3. Update the version date
4. Follow semantic versioning (MAJOR.MINOR.PATCH)
