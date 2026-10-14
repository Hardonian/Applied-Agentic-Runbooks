"""
Main CLI entry point for Agent Factory Platform.
"""

import sys
import typer
from typing import Optional

# Ensure safe console encoding on Windows hosts
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent_factory.cli.commands import agent, tool, workflow, blueprint, registry, marketplace, doctor, config, docs

app = typer.Typer(
    name="agent-factory",
    help="Agent Factory Platform - Build AI agents in minutes",
    add_completion=False,
)

# Add command groups
app.add_typer(agent.app, name="agent")
app.add_typer(tool.app, name="tool")
app.add_typer(workflow.app, name="workflow")
app.add_typer(blueprint.app, name="blueprint")
app.add_typer(registry.app, name="registry")
app.add_typer(marketplace.app, name="marketplace")
app.add_typer(doctor.app, name="doctor")
app.add_typer(config.app, name="config")
app.add_typer(docs.app, name="docs")

# Add execution commands
from agent_factory.cli.commands.execution import app as execution_app
app.add_typer(execution_app, name="execution")

# Add new command groups
from agent_factory.cli.commands import notebook, promptlog, eval, ui, saas, metrics, export
app.add_typer(notebook.app, name="notebook")
app.add_typer(promptlog.app, name="promptlog")
app.add_typer(eval.app, name="eval")
app.add_typer(ui.app, name="ui")
app.add_typer(saas.app, name="saas")
app.add_typer(metrics.app, name="metrics")
app.add_typer(export.app, name="export")


@app.command()
def version():
    """Show version information."""
    from agent_factory import __version__
    typer.echo(f"Agent Factory Platform v{__version__}")


@app.command()
def init(
    project_name: str = typer.Option("my_agent_project", "--name", "-n", help="Project name"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project path"),
):
    """Initialize a new Agent Factory project."""
    import os
    from pathlib import Path
    
    project_path = Path(path) if path else Path(project_name)
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create directory structure
    (project_path / "agents").mkdir(exist_ok=True)
    (project_path / "tools").mkdir(exist_ok=True)
    (project_path / "workflows").mkdir(exist_ok=True)
    (project_path / "blueprints").mkdir(exist_ok=True)
    
    # Create .env.example
    env_example = """# Agent Factory Configuration
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Environment
ENVIRONMENT=development
"""
    (project_path / ".env.example").write_text(env_example)
    
    # Create README
    readme = f"""# {project_name}

Agent Factory project.

## Quick Start

1. Copy `.env.example` to `.env` and add your API keys
2. Create agents: `agent-factory agent create`
3. Run agents: `agent-factory agent run <agent-id>`
"""
    (project_path / "README.md").write_text(readme)
    
    typer.echo(f"✅ Project initialized at {project_path.absolute()}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host address"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Auto reload"),
):
    """
    Launch Agent Factory API and Visual Studio web dashboard.
    """
    import uvicorn
    typer.echo(f"🚀 Starting Agent Factory Studio at http://{host}:{port}")
    typer.echo(f"🎨 Studio UI Dashboard: http://{host}:{port}/studio")
    typer.echo(f"📚 OpenAPI Documentation: http://{host}:{port}/docs")
    uvicorn.run("agent_factory.api.main:app", host=host, port=port, reload=reload)


@app.command()
def chat(
    agent_id: str = typer.Argument("default", help="Agent ID to chat with"),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="Target LLM model"),
):
    """
    Start interactive terminal chat session with an agent.
    """
    from agent_factory.agents.agent import Agent
    from agent_factory.integrations.universal_client import UniversalLLMClient
    
    typer.echo(f"💬 Agent Factory Interactive Chat Session [{agent_id}] (Model: {model})")
    typer.echo("Type 'exit' or 'quit' to terminate.\n" + "=" * 50)
    
    agent = Agent(id=agent_id, name=agent_id, instructions=f"You are {agent_id}, a helpful assistant.", model=model)
    
    while True:
        try:
            user_input = input("\n👤 You: ")
            if user_input.strip().lower() in {"exit", "quit"}:
                typer.echo("👋 Goodbye!")
                break
            if not user_input.strip():
                continue
                
            res = agent.run(user_input)
            if res.reasoning_content:
                typer.echo(f"\n🧠 Thinking:\n{res.reasoning_content}")
            typer.echo(f"\n🤖 {agent_id}: {res.output}")
        except (KeyboardInterrupt, EOFError):
            typer.echo("\n👋 Exiting chat.")
            break


@app.command()
def audit(
    agent_id: str = typer.Argument(..., help="Agent ID to scan"),
):
    """
    Run automated OWASP Top 10 for LLMs security audit scan on an agent.
    """
    from agent_factory.agents.agent import Agent
    from agent_factory.security.owasp_scanner import OWASPSecurityScanner
    
    agent = Agent(id=agent_id, name=agent_id, instructions="Autonomous agent instance.")
    report = OWASPSecurityScanner.audit_agent(agent)
    
    typer.echo(f"\n🛡️  OWASP Top 10 Security Audit Report for Agent: [{agent_id}]")
    typer.echo(f"Score: {report.score}/100 | Status: {report.overall_status}")
    typer.echo("-" * 60)
    for check in report.checks:
        typer.echo(f"[{check.status}] {check.category_id}: {check.name} - {check.details}")


@app.command()
def pack(
    blueprint_dir: str = typer.Argument(..., help="Path to blueprint directory"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .afpkg path"),
):
    """
    Pack a blueprint into a cryptographically signed .afpkg archive.
    """
    from pathlib import Path
    from agent_factory.marketplace.packager import BlueprintPackager, PackageManifest
    
    src = Path(blueprint_dir)
    if not src.exists():
        typer.echo(f"❌ Directory not found: {src}", err=True)
        raise typer.Exit(1)
        
    out = Path(output) if output else src.with_suffix(".afpkg")
    manifest = PackageManifest(
        id=src.name,
        name=src.name.replace("_", " ").title(),
        version="1.0.0",
        author="Agent Factory Creator",
        description=f"Packaged blueprint from {src.name}",
    )
    
    out_path, checksum = BlueprintPackager.pack_directory(src, out, manifest)
    typer.echo(f"📦 Successfully packaged [{src.name}] into {out_path}")
    typer.echo(f"🔑 SHA-256 Checksum: {checksum}")


@app.command()
def certify(
    agent_id: str = typer.Argument(..., help="Agent ID to certify"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Export path for certification Markdown report"),
):
    """
    Generate an enterprise audit compliance certificate (SOC 2, HIPAA, EU AI Act, OWASP) for an agent.
    """
    from agent_factory.agents.agent import Agent
    from agent_factory.compliance.certification import AgentCertificationGenerator
    from agent_factory.core.guardrails import Guardrails, SQLInjectionGuardrail

    guardrails = Guardrails()
    guardrails.add_input_guardrail(SQLInjectionGuardrail())
    agent = Agent(id=agent_id, name=agent_id, instructions=f"Enterprise Agent {agent_id}", guardrails=guardrails)
    cert = AgentCertificationGenerator.generate_certificate(agent)

    typer.echo(f"\n[CERTIFICATION] Agent Factory Compliance Record: [{agent_id}]")
    typer.echo(f"Certificate ID : {cert.certificate_id}")
    typer.echo(f"Grade          : {cert.grade.value} ({cert.overall_score}/100)")
    typer.echo(f"Risk Tier      : {cert.risk_tier.value}")
    typer.echo(f"Integrity Hash : {cert.integrity_hash[:24]}...")
    typer.echo(f"Digital Seal   : {cert.digital_seal[:24]}...")
    typer.echo(f"OWASP Score    : {cert.owasp_score}/100")
    typer.echo("-" * 60)
    for ev in cert.evidence_trail:
        typer.echo(f"[{ev.status}] {ev.framework} {ev.control_id}: {ev.control_name}")

    if output:
        from pathlib import Path
        out_file = Path(output)
        out_file.write_text(cert.to_markdown(), encoding="utf-8")
        typer.echo(f"\n[SAVED] Audit certification document: {out_file.resolve()}")


@app.command()
def swarm(
    task: str = typer.Argument(..., help="Task prompt for the multi-agent swarm"),
    pattern: str = typer.Option("hierarchical", "--pattern", "-p", help="Swarm pattern (hierarchical, peer_debate, voting_consensus, dynamic_router)"),
):
    """
    Execute a collaborative multi-agent swarm on a complex task.
    """
    from agent_factory.agents.agent import Agent
    from agent_factory.orchestration.swarm import SwarmOrchestrator, SwarmPattern

    swarm_agents = [
        Agent(id="researcher", name="Researcher", instructions="Conduct background analysis."),
        Agent(id="analyst", name="Analyst", instructions="Evaluate risks and trade-offs."),
        Agent(id="synthesizer", name="Synthesizer", instructions="Formulate final recommendations."),
    ]
    supervisor = Agent(id="supervisor", name="Supervisor", instructions="Lead and coordinate team.")

    orchestrator = SwarmOrchestrator(
        agents=swarm_agents,
        supervisor=supervisor,
        pattern=SwarmPattern(pattern),
    )
    res = orchestrator.execute(task)
    typer.echo(f"\n[SWARM] Multi-Agent Swarm Execution Complete ({pattern}):")
    typer.echo(f"Status: {res.status.value} | Execution Time: {res.execution_time:.2f}s")
    typer.echo("-" * 60)
    typer.echo(res.final_output)


@app.command()
def mcts(
    problem: str = typer.Argument(..., help="Problem statement to explore via MCTS"),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum tree search depth"),
    simulations: int = typer.Option(8, "--simulations", "-s", help="Number of Monte Carlo simulations"),
):
    """
    Execute Speculative Monte Carlo Tree Search (MCTS) reasoning across multi-path hypotheses.
    """
    from agent_factory.reasoning.mcts import SpeculativeMCTSEngine

    engine = SpeculativeMCTSEngine(max_depth=depth, num_simulations=simulations)
    res = engine.search(problem)
    typer.echo(f"\n[MCTS] Speculative Tree Search Complete:")
    typer.echo(f"Confidence: {res.confidence_score*100:.1f}% | Nodes: {res.total_nodes_explored} | Pruned: {res.branches_pruned} | Depth: {res.depth_reached}")
    typer.echo("-" * 60)
    for idx, step in enumerate(res.best_trajectory, 1):
        typer.echo(f"{idx}. {step}")
    typer.echo(f"\n[SOLUTION]:\n{res.final_solution}")


@app.command()
def cascade(
    prompt: str = typer.Argument(..., help="Prompt to execute via Speculative Model Cascade"),
    tier: Optional[str] = typer.Option(None, "--tier", "-t", help="Force model tier (fast, standard, deep)"),
):
    """
    Execute prompt via Speculative Model Cascade optimizing for Pareto cost and latency.
    """
    from agent_factory.optimization.cascade_router import SpeculativeCascadeRouter, ModelTier

    tier_enum = ModelTier(tier) if tier else None
    router = SpeculativeCascadeRouter()
    res = router.execute(prompt, force_tier=tier_enum)
    typer.echo(f"\n[CASCADE] Pareto Optimization Complete:")
    typer.echo(f"Tier: {res.tier_used.value.upper()} ({res.model_used}) | Speculative Draft: {'ACCEPTED' if res.speculative_draft_accepted else 'ESCALATED'}")
    typer.echo(f"Cost Savings: {res.cost_savings_percentage:.1f}% | Latency Speedup: {res.speedup_factor:.1f}x (${res.cost_usd:.6f} vs ${res.frontier_baseline_cost_usd:.6f})")
    typer.echo("-" * 60)
    typer.echo(res.output)


if __name__ == "__main__":
    app()
