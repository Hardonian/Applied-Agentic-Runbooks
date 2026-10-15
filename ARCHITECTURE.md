# Agent Factory Platform - Complete Architecture & Directory Tree

## Enterprise Platform Trinity

The platform joins evaluation, live operations, and deployment through one evidence
contract. `agent_factory.evaluation.arena.ArenaRunner` executes five deterministic,
offline-capable suites: reasoning frontier, Pareto model cascade, adversarial MCPWall,
self-healing fault injection, and Settler accounting. Every summary embeds a VeriDAG
Merkle proof and AgentPCAP capture; the REST leaderboard ranks their pass rate, Pareto
score, and tail latency.

`agent_factory.api.ws` supplies a bounded in-process pub/sub bus. `/api/v1/ws/stream`
handles token chunks and operator approval decisions, while `/api/v1/ws/arena` carries
suite progress, tree/capture telemetry, and final summaries. Slow consumers lose only
their oldest queued event and cannot block producers. Studio 2.0 consumes these same
contracts and uses external `style.css` exclusively.

`agent_factory.telemetry.otel_exporter` maps AgentPCAP frames to OTLP log records,
VeriDAG transitions to OTLP spans, and native counters to Prometheus exposition text.
No OpenTelemetry SDK is required and export is a safe no-op without an endpoint. The
`deploy/` tree provides a complete Compose stack, provisioned observability, a Helm
chart with autoscaling and health gates, and an air-gapped local-model overlay.

```text
ArenaRunner ── events ──> EventBus ──> REST/WebSocket ──> Studio
     │                       │
     ├── VeriDAG proof       └── OTel Collector / Prometheus / Jaeger
     └── AgentPCAP capture
```

### Durable multi-replica control plane

`ArenaService` writes the queued record before starting work. `ArenaRepository` uses
the configured SQLAlchemy engine, providing SQLite development and PostgreSQL
production behavior. Every run has a tenant, request, lifecycle timestamps, retention
deadline, cooperative cancellation flag, terminal summary, and immutable artifact
references. Redis Streams is an optional transport layered beneath the local bounded
bus; sequence cursors provide replay after reconnect while the REST record remains the
source of truth.

The MCPWall approval authority persists tickets separately from WebSocket connections.
Decisions enforce tenant boundaries, operator roles, separation of duty, expiry, and
single consumption, then issue an HMAC-SHA256 receipt. Arena evidence uses an
independent signing key and manifest so third parties can verify captures and Merkle
transitions without database or model access.

## Full Directory Structure

```
agent-factory-platform/
├── agent_factory/                    # Core Python package
│   ├── __init__.py                   # Package exports
│   ├── core/                         # Core primitives
│   │   ├── __init__.py
│   │   ├── agent.py                  # Agent class with lifecycle management
│   │   ├── tool.py                   # Tool interface and decorator
│   │   ├── workflow.py               # Workflow orchestration engine
│   │   ├── blueprint.py              # Blueprint definition and packaging
│   │   ├── memory.py                 # Memory/session management
│   │   └── guardrails.py             # Safety and validation
│   ├── registry/                     # Registry system
│   │   ├── __init__.py
│   │   ├── local_registry.py         # Local file-based registry
│   │   └── remote_registry.py       # Remote API registry (marketplace)
│   ├── runtime/                      # Execution engine
│   │   ├── __init__.py
│   │   ├── engine.py                 # Agent/workflow execution engine
│   │   └── scheduler.py             # Task scheduling
│   ├── integrations/                 # Pre-built integrations
│   │   ├── __init__.py
│   │   ├── openai/                   # OpenAI Agents SDK wrapper
│   │   ├── anthropic/                # Claude API integration
│   │   ├── crewai/                   # CrewAI integration
│   │   ├── tools/                    # Tool implementations
│   │   │   ├── web_search.py
│   │   │   ├── file_io.py
│   │   │   ├── calculator.py
│   │   │   ├── slack.py
│   │   │   └── email.py
│   │   └── mcp/                      # MCP server integrations
│   ├── api/                          # FastAPI REST API
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── agents.py             # Agent endpoints
│   │       ├── tools.py              # Tool endpoints
│   │       ├── workflows.py          # Workflow endpoints
│   │       ├── blueprints.py         # Blueprint endpoints
│   │       └── executions.py         # Execution endpoints
│   ├── cli/                          # CLI interface
│   │   ├── __init__.py
│   │   ├── main.py                   # Typer CLI entry point
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── agent.py              # agent create/list/run/delete
│   │       ├── tool.py               # tool register/list/test
│   │       ├── workflow.py           # workflow create/run/deploy
│   │       ├── blueprint.py         # blueprint create/publish/install
│   │       └── registry.py          # registry search/install
│   └── utils/                        # Shared utilities
│       ├── __init__.py
│       ├── config.py                 # Configuration management
│       └── logging.py                # Structured logging
├── blueprints/                       # Blueprint definitions (YAML/JSON)
│   ├── support_bot/
│   │   └── blueprint.yaml
│   └── research_assistant/
│       └── blueprint.yaml
├── examples/                         # Refactored notebook examples
│   ├── basic_agent.py                # Basic agent example
│   ├── multi_agent_system.py         # Multi-agent coordination
│   └── customer_support_bot.py       # Support bot template
├── tests/                            # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                             # Documentation
│   ├── VISION_AND_STRATEGY.md        # Strategic vision
│   ├── GTM_PLAN.md                   # Go-to-market plan
│   ├── PRICING_TIERS.md              # Pricing strategy
│   ├── USE_CASE_BLUEPRINTS.md        # Blueprint catalog
│   ├── api/                          # API documentation
│   └── guides/                       # User guides
├── scripts/                          # Utility scripts
│   ├── migrate_notebooks.py          # Convert notebooks to examples
│   └── generate_blueprint.py
├── docker/                           # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── pyproject.toml                    # Python package config
├── README.md                         # Main README
├── ARCHITECTURE.md                   # This file
└── LICENSE                           # GPL-3.0 License
```

## Key Components

### Core Library (`agent_factory/core/`)

**Agent** (`agent.py`):
- Core agent class with OpenAI SDK integration
- Memory and guardrails support
- Handoff capabilities for multi-agent systems
- Serialization/deserialization

**Tool** (`tool.py`):
- Abstract tool interface
- `@function_tool` decorator for easy tool creation
- Parameter validation and schema generation
- Tool metadata and discovery

**Workflow** (`workflow.py`):
- Multi-step workflow orchestration
- Conditional branching
- Input/output mapping between steps
- Trigger support (webhook, schedule, event)

**Blueprint** (`blueprint.py`):
- Blueprint definition format (YAML/JSON)
- Packaging and installation system
- Pricing model support
- Dependency management

**Memory** (`memory.py`):
- Abstract memory store interface
- SQLite implementation for sessions
- Conversation history management

**Guardrails** (`guardrails.py`):
- Input/output validation
- Safety checks (profanity, SQL injection, PII)
- Configurable guardrail system

### Registry System (`agent_factory/registry/`)

**LocalRegistry**:
- File-based storage for agents, tools, workflows, blueprints
- Search and discovery
- CRUD operations

**RemoteRegistry**:
- Marketplace API client
- Blueprint search and installation
- Publishing to marketplace

### Runtime Engine (`agent_factory/runtime/`)

**RuntimeEngine**:
- Agent and workflow execution
- Execution tracking and history
- Error handling and retries

**Scheduler**:
- Scheduled agent/workflow execution
- Cron-like scheduling
- Background task management

### CLI Interface (`agent_factory/cli/`)

**Commands**:
- `agent-factory init` - Initialize project
- `agent-factory agent create/list/run/delete` - Agent management
- `agent-factory tool register/list` - Tool management
- `agent-factory workflow create/run` - Workflow management
- `agent-factory blueprint install/list/search` - Blueprint management
- `agent-factory registry search` - Registry search

### REST API (`agent_factory/api/`)

**Endpoints**:
- `POST /api/v1/agents/` - Create agent
- `GET /api/v1/agents/` - List agents
- `GET /api/v1/agents/{id}` - Get agent
- `POST /api/v1/agents/{id}/run` - Run agent
- `DELETE /api/v1/agents/{id}` - Delete agent
- Similar endpoints for tools, workflows, blueprints, executions

## Design Principles

1. **Composability**: Agents, tools, and workflows are composable building blocks
2. **Extensibility**: Easy to add custom tools, integrations, and agents
3. **Production-Ready**: Built-in observability, scaling, security
4. **Developer Experience**: Clean Python API, comprehensive docs, CLI tooling
5. **Monetization**: Blueprint system enables marketplace and SaaS models

## Migration Path

1. **Extract Patterns**: Identify reusable patterns from notebooks
2. **Create Primitives**: Build Agent, Tool, Workflow classes
3. **Refactor Examples**: Convert notebook cells to Python scripts
4. **Create Blueprints**: Package common patterns as Blueprint YAML files
5. **Build Interfaces**: Add CLI and API for programmatic access
6. **Add Registry**: Enable discovery and sharing of components

## Next Steps

1. Integrate with OpenAI Agents SDK (replace placeholder implementations)
2. Add more tool integrations (Slack, email, databases)
3. Build Blueprint marketplace backend
4. Add authentication and authorization to API
5. Create comprehensive test suite
6. Write user documentation and guides
7. Set up CI/CD pipeline

---

**Status**: ✅ Complete skeleton generated. Ready for implementation and integration.
