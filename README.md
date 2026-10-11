# Agent Factory

**Build production-ready AI agents in minutes, not months.**

Agent Factory is the platform that turns your AI prototypes into real products. Stop wrestling with infrastructure. Start building agents that matter.

---

> **🤖 This repo audits itself.** Seven readiness audits run unattended every night at 03:00 UTC, and the diff lands as a PR this repo opens itself — 320 consecutive green nights, zero gaps, verified. How it works: [docs/RUNBOOK.md](docs/RUNBOOK.md)


## 🎯 One-Sentence Pitch

Agent Factory gives you everything you need to build, deploy, and monetize AI agents—from prototype to production—without the usual headaches.

---

## 💡 Why This Exists

You've been there. You prototype an AI agent in a Jupyter notebook. It works beautifully. People love it. "When can we use this?" they ask.

Then reality hits.

To turn that prototype into something real, you need conversation handling, error recovery, observability, authentication, rate limiting, billing, multi-tenancy, APIs, deployment infrastructure... Suddenly your simple idea needs a team of engineers and months of work.

**Most projects never make it past this point.**

Agent Factory fixes that. We've built the infrastructure. We've handled the complexity. You focus on what makes your agent unique. We handle the rest.

---

## 🚀 Value Proposition

**For Developers:** Ship faster. Build production-ready agents without becoming an infrastructure expert.

**For Founders:** Launch your SaaS faster. We handle billing, multi-tenancy, and scaling so you can focus on users.

**For Researchers & Educators:** Build tools that help people without getting lost in technical details.

**For Teams:** Automate workflows, build internal tools, create customer-facing agents—all on a platform that scales from prototype to production.

---

## ✨ Key Features

**🧩 Composable Building Blocks**
- Create agents with natural language instructions
- Add tools and capabilities as you need them
- Chain agents together into workflows
- Everything works together seamlessly

**🏭 Production Ready, Out of the Box**
- Built-in memory and conversation context
- Error handling and automatic retries
- Observability and structured logging
- Rate limiting and security built-in

**📦 Blueprint System**
- Install pre-built agent configurations
- Share your own creations
- Build on what others have made
- Skip the setup, start building

**🔌 Multiple Ways to Use**
- Python library for developers
- CLI for quick prototyping
- REST API for integrations
- SDK for programmatic access

---

## 🎬 Real-World Use Cases

**Customer Support Bots**
Build bots that actually help customers. Handle common questions, escalate when needed, learn from every interaction. Perfect for e-commerce, SaaS, and service businesses.

**Research Assistants**
Create agents that help researchers find papers, summarize findings, organize information. Perfect for academic teams, knowledge workers, and content creators.

**Educational Tools**
Build personalized learning assistants that adapt to each student. Generate practice questions, explain concepts, track progress. Transform how students learn.

**Internal Automation**
Automate repetitive workflows. Process documents, route requests, generate reports—all with agents that understand context. Free your team from busywork.

**SaaS Products**
Turn your agent into a product. We handle billing, multi-tenancy, and scaling so you can focus on your users. Launch faster, scale easier.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
├─────────────────────────────────────────────────────────────┤
│  Python SDK  │  CLI  │  REST API  │  Blueprints            │
├─────────────────────────────────────────────────────────────┤
│              Agent Factory Platform                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │  Agents  │  │  Tools   │  │Workflows │                │
│  └──────────┘  └──────────┘  └──────────┘                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ Registry │  │ Runtime  │  │Telemetry │                │
│  └──────────┘  └──────────┘  └──────────┘                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ Security │  │ Billing  │  │Knowledge │                │
│  └──────────┘  └──────────┘  └──────────┘                │
├─────────────────────────────────────────────────────────────┤
│  OpenAI  │  Anthropic  │  Custom Integrations             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚦 Quick Start

### Installation

```bash
pip install agent-factory
```

### Your First Agent (30 seconds)

```python
from agent_factory import Agent, function_tool

@function_tool
def calculate(expression: str) -> float:
    """Calculate mathematical expressions."""
    return eval(expression)

agent = Agent(
    id="calculator",
    name="Calculator Agent",
    instructions="You are a helpful calculator assistant.",
    tools=[calculate],
)

result = agent.run("What's 15% tip on $87.50?")
print(result.output)
```

### Using the CLI

```bash
# Create an agent
agent-factory agent create calculator \
  --name "Calculator Agent" \
  --instructions "You help with math"

# Run it
agent-factory agent run calculator --input "Calculate 20% of 100"
```

### Using the API

```bash
# Start the server
uvicorn agent_factory.api.main:app --reload

# Create an agent
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "calculator",
    "name": "Calculator Agent",
    "instructions": "You help with math"
  }'
```

**👉 [Get Started Guide](docs/GETTING_STARTED.md)** — Detailed setup and first steps

---

## 📁 Project Structure

```
agent_factory/
├── core/              # Core primitives (Agent, Tool, Workflow)
├── agents/            # Agent implementations
├── tools/             # Tool system
├── workflows/         # Workflow orchestration
├── blueprints/        # Blueprint system
├── registry/          # Local and remote registries
├── runtime/           # Execution engine
├── api/               # REST API
├── cli/               # Command-line interface
├── sdk/               # Python SDK
├── telemetry/         # Analytics and metrics
├── security/          # Auth, RBAC, audit logging
├── billing/           # Usage tracking and billing
└── integrations/       # LLM providers and tools
```

---

## 🎓 Education Focus

Agent Factory is designed with education in mind. We partner with institutions to build tools that help students learn and teachers teach.

**Education Use Cases:**
- Virtual teaching assistants available 24/7
- Personalized learning paths that adapt to each student
- Research assistants that help with citations and papers
- Assessment tools that generate and grade questions
- Career guidance and professional development

**Partnership:** We work with McGraw Hill Education and other partners to bring AI tools to educational institutions. [Learn more →](https://www.mheducation.ca/partnerships)

---

## 📚 Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** — Your first 10 minutes with Agent Factory
- **[User Guide](docs/USER_GUIDE.md)** — Complete feature documentation
- **[Architecture](docs/ARCHITECTURE_DETAILED.md)** — Deep dive into how it works
- **[API Reference](docs/API_REFERENCE.md)** — REST API documentation
- **[Use Cases](USE_CASES.md)** — Real-world examples and patterns
- **[Value Proposition](VALUE_PROPOSITION.md)** — Why Agent Factory exists

### 🗄️ Database & Backend

- **[Stack Discovery](docs/stack-discovery.md)** — **Complete stack inventory and architecture overview**
- **[Backend Strategy](docs/backend-strategy.md)** — **Canonical backend choice and rationale**
- **[Supabase Setup Guide](docs/supabase-setup.md)** — Complete Supabase configuration guide
- **[Backend Discovery](docs/backend-discovery.md)** — Database setup and migration framework overview
- **[Data Model Overview](docs/data-model-overview.md)** — Complete schema documentation
- **[Backend Options & Costs](docs/backend-options-and-costs.md)** — Supabase vs alternatives analysis
- **[Migrations Workflow](docs/migrations-workflow.md)** — How to run and create migrations

### 🚀 Development & Deployment

- **[Local Development](docs/local-dev.md)** — **Complete local setup guide**
- **[CI/CD Overview](docs/ci-overview.md)** — **CI workflows and required checks**
- **[Environment & Secrets](docs/env-and-secrets.md)** — **Environment variables guide**
- **[Frontend Hosting Strategy](docs/frontend-hosting-strategy.md)** — **API-first platform (no frontend)**
- **[Demo Script](docs/demo-script.md)** — **Step-by-step demo guide**

---

## 🛠️ Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linters
ruff check agent_factory/ tests/
black --check agent_factory/ tests/

# Type checking
mypy agent_factory/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

---

## 🤝 Community

**Getting Help:**
- Open an issue on GitHub for bugs or feature requests
- Check existing issues and discussions
- Read the documentation

**Contributing:**
We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Partnerships:**
Interested in partnering? Reach out at partnerships@agentfactory.io

---

## 📄 License

GPL-3.0 License — see [LICENSE](LICENSE) file.

---

## 🔗 Links

- [Documentation](https://docs.agentfactory.io)
- [Marketplace](https://marketplace.agentfactory.io)
- [GitHub](https://github.com/agentfactory/platform)
- [McGraw Hill Education Partnerships](https://www.mheducation.ca/partnerships)

---

## 🎯 YC Readiness

**For Y Combinator applicants and investors:**

Comprehensive YC readiness assessment and preparation materials are available in the `/yc/` directory:

- **[YC Readiness Package](yc/README.md)** - Complete guide to YC preparation
- **[Product Overview](yc/YC_PRODUCT_OVERVIEW.md)** - Product narrative and value proposition
- **[Gap Analysis](yc/YC_GAP_ANALYSIS.md)** - What's missing and how to fix it
- **[Interview Cheat Sheet](yc/YC_INTERVIEW_CHEATSHEET.md)** - Interview preparation guide
- **[Metrics Checklist](yc/YC_METRICS_CHECKLIST.md)** - What metrics YC asks for

**Quick Start:** See [yc/README.md](yc/README.md) for overview and next steps.

---

**Built by developers, for developers.**  
**Making AI agents accessible to everyone.**

---

## 👤 About the Founder

**Scott Hardie** - Founder, CEO & Operator

After 15+ years helping institutions deploy AI-powered learning platforms at McGraw Hill and Pearson Education, I saw the same problem again and again: great AI prototypes stuck in Jupyter notebooks, unable to reach production because developers couldn't build the infrastructure.

I've built multiple AI-driven systems myself—Hardonia OS, PromptPilot, Daily Intel Suite—and hit the same wall every time: the AI worked, but deploying it required months of infrastructure work.

**Agent Factory exists because I've lived this problem.** We've built the infrastructure so you don't have to.

- **Email:** scottrmhardie@gmail.com
- **GitHub:** [shardie-github](https://github.com/shardie-github)
- **LinkedIn:** [scottrmhardie](https://www.linkedin.com/in/scottrmhardie)

---

## ⭐ Star Us

If Agent Factory helps you build something amazing, consider giving us a star on GitHub. It helps others discover the project.

---

## 🎯 Your First 10 Minutes

1. **Install:** `pip install agent-factory`
2. **Create your first agent:** See the Quick Start section above
3. **Explore examples:** Check out the [examples/](examples/) directory
4. **Read the docs:** Start with [Getting Started](docs/GETTING_STARTED.md)
5. **Build something:** Turn your idea into reality

---

## 🚀 Who This Is For

**You're a developer** who wants to ship AI products faster without building infrastructure from scratch.

**You're a founder** building a SaaS and need billing, multi-tenancy, and scaling handled.

**You're a researcher or educator** with domain expertise who wants to build tools without becoming an infrastructure expert.

**You're a team** that needs to automate workflows, build internal tools, or create customer-facing agents.

**If you've ever had a great idea stuck in a Jupyter notebook, Agent Factory is for you.**
