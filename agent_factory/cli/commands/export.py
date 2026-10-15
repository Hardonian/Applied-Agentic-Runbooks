"""
CLI commands for exporting data.
"""

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

import typer

from agent_factory.telemetry import get_analytics

try:
    from agent_factory.telemetry.revenue import get_revenue_tracker
except ImportError:
    get_revenue_tracker = None  # type: ignore[assignment]

app = typer.Typer(name="export", help="Export metrics and data")


@app.command()
def metrics(
    output_file: str = typer.Option("metrics_export.json", help="Output file path"),
    format: str = typer.Option("json", help="Export format (json, csv)"),
    days: int = typer.Option(30, help="Number of days to export"),
):
    """
    Export metrics to file.
    
    Example:
        agent-factory export metrics --output metrics.json --format json --days 30
    """
    analytics = get_analytics()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get all metrics
    metrics_data = {
        "export_date": datetime.utcnow().isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "growth_summary": analytics.get_growth_summary(start_date, end_date),
        "conversion_funnel": analytics.get_conversion_funnel(start_date, end_date),
        "channel_attribution": analytics.get_channel_attribution(start_date, end_date),
        "growth_rates": {
            "users": analytics.get_growth_rate("users", "month"),
            "tenants": analytics.get_growth_rate("tenants", "month"),
            "agent_runs": analytics.get_growth_rate("agent_runs", "month"),
            "revenue": analytics.get_growth_rate("revenue", "month"),
        },
    }
    
    # Add revenue metrics if available
    if get_revenue_tracker is not None:
        try:
            revenue_tracker = get_revenue_tracker()
            metrics_data["revenue"] = {
                "mrr": revenue_tracker.get_mrr(),
                "arr": revenue_tracker.get_arr(),
                "by_type": revenue_tracker.get_revenue_by_type(start_date, end_date),
                "by_plan": revenue_tracker.get_revenue_by_plan(start_date, end_date),
            }
        except Exception as e:
            typer.echo(f"Warning: Could not get revenue metrics: {e}", err=True)
    
    # Export to file
    output_path = Path(output_file)
    
    if format == "json":
        with open(output_path, "w") as f:
            json.dump(metrics_data, f, indent=2, default=str)
        typer.echo(f"✅ Metrics exported to {output_path}")
    elif format == "csv":
        # Flatten metrics for CSV
        csv_data = []
        for key, value in metrics_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    csv_data.append({
                        "metric": f"{key}.{sub_key}",
                        "value": sub_value,
                    })
            else:
                csv_data.append({
                    "metric": key,
                    "value": value,
                })
        
        with open(output_path, "w", newline="") as f:
            if csv_data:
                writer = csv.DictWriter(f, fieldnames=["metric", "value"])
                writer.writeheader()
                writer.writerows(csv_data)
        typer.echo(f"✅ Metrics exported to {output_path}")
    else:
        typer.echo(f"❌ Unknown format: {format}", err=True)
        raise typer.Exit(1)


@app.command()
def funnel(
    output_file: str = typer.Option("funnel_export.json", help="Output file path"),
    days: int = typer.Option(30, help="Number of days to export"),
):
    """
    Export conversion funnel data.
    
    Example:
        agent-factory export funnel --output funnel.json --days 30
    """
    analytics = get_analytics()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    funnel_data = analytics.get_conversion_funnel(start_date, end_date)
    
    output_path = Path(output_file)
    with open(output_path, "w") as f:
        json.dump(funnel_data, f, indent=2, default=str)
    
    typer.echo(f"✅ Funnel data exported to {output_path}")


@app.command()
def channels(
    output_file: str = typer.Option("channels_export.json", help="Output file path"),
    days: int = typer.Option(30, help="Number of days to export"),
):
    """
    Export channel attribution data.
    
    Example:
        agent-factory export channels --output channels.json --days 30
    """
    get_analytics()
    
    end_date = datetime.utcnow()
    end_date - timedelta(days=days)
    
@app.command(name="agent")
def export_agent_command(
    agent_id: str = typer.Argument(..., help="Agent ID to export"),
    target: str = typer.Option("langgraph", "--target", "-t", help="Target framework (langgraph, crewai, autogen, llamaindex, docker, openai)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """
    Export an agent to LangGraph, CrewAI, AutoGen, LlamaIndex, Docker, or OpenAI specs.
    
    Example:
        agent-factory export agent research_assistant --target langgraph
    """
    from agent_factory.agents.agent import Agent
    from agent_factory.interop import export_agent
    from agent_factory.registry.local_registry import LocalRegistry
    
    registry = LocalRegistry()
    agent_obj = registry.get_agent(agent_id)
    if not agent_obj:
        # Create a mock agent representation for export if not in local registry
        agent_obj = Agent(
            id=agent_id,
            name=agent_id.replace("_", " ").title(),
            instructions=f"Autonomous Agent Factory instance for {agent_id}.",
            model="gpt-4o",
        )
        
    exported_code = export_agent(agent_obj, target_framework=target)
    
    if output:
        out_p = Path(output)
        out_p.write_text(exported_code, encoding="utf-8")
        typer.echo(f"✅ Exported {agent_id} to {target} at {out_p.absolute()}")
    else:
        typer.echo(f"\n--- Exported {agent_id} ({target}) ---\n")
        typer.echo(exported_code)

