"""
CLI commands for evaluation, benchmarking, and autotune.
"""

import typer

from agent_factory.eval import BenchmarkRunner, autotune_agent
from agent_factory.eval.model import BenchmarkSuite, Scenario

app = typer.Typer(name="eval", help="Evaluation, benchmarking, and autotune commands")


@app.command()
def benchmark(
    agent_id: str = typer.Argument(..., help="Agent ID to benchmark"),
    suite_id: str = typer.Option("baseline", "--suite", "-s", help="Benchmark suite ID"),
):
    """Run benchmark suite against an agent."""
    # TODO: Load suite from file or registry
    suite = BenchmarkSuite(
        id=suite_id,
        name="Baseline Suite",
        scenarios=[
            Scenario(
                id="test-1",
                name="Test Scenario",
                inputs={"query": "test"},
            ),
        ],
    )

    runner = BenchmarkRunner()
    results = runner.run_benchmark(agent_id, suite)

    typer.echo(f"\nBenchmark Results for {agent_id}:")
    typer.echo(f"  Scenarios: {len(results)}")
    typer.echo(f"  Successful: {sum(1 for r in results if r.success)}")
    typer.echo(f"  Failed: {sum(1 for r in results if not r.success)}")

    if results:
        avg_latency = sum(r.latency for r in results) / len(results)
        typer.echo(f"  Avg Latency: {avg_latency:.2f}s")


@app.command()
def stress_test(
    agent_id: str = typer.Argument(..., help="Agent ID to stress test"),
    concurrent: int = typer.Option(10, "--concurrent", "-c", help="Concurrent requests"),
    duration: int = typer.Option(60, "--duration", "-d", help="Duration in seconds"),
):
    """Run stress test (load testing) on an agent."""
    runner = BenchmarkRunner()
    results = runner.stress_test(agent_id, concurrent, duration)

    typer.echo(f"\nStress Test Results for {agent_id}:")
    typer.echo(f"  Concurrent Requests: {results['concurrent_requests']}")
    typer.echo(f"  Duration: {results['duration']}s")
    typer.echo(f"  Total Requests: {results['total_requests']}")
    typer.echo(f"  Successful: {results['successful_requests']}")
    typer.echo(f"  Failed: {results['failed_requests']}")
    typer.echo(f"  Avg Latency: {results['avg_latency']:.2f}s")


@app.command()
def autotune(
    agent_id: str = typer.Argument(..., help="Agent ID to autotune"),
    suite_id: str = typer.Option("baseline", "--suite", "-s", help="Benchmark suite ID"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output config file"),
):
    """Automatically tune agent configuration."""
    # TODO: Load suite from file or registry
    suite = BenchmarkSuite(
        id=suite_id,
        name="Baseline Suite",
        scenarios=[
            Scenario(
                id="test-1",
                name="Test Scenario",
                inputs={"query": "test"},
            ),
        ],
    )

    output_path = output or f"./agent_factory/agents/{agent_id}_tuned.yaml"

    try:
        tuned_config = autotune_agent(agent_id, suite, output_path=output_path)
        typer.echo("✅ Autotune complete!")
        typer.echo(f"   Tuned config saved to: {output_path}")
        typer.echo(f"   Temperature: {tuned_config.temperature}")
        typer.echo(f"   Max Tokens: {tuned_config.max_tokens}")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1) from e
