"""
Workflow visualization - Generate Mermaid/Graphviz diagrams.
"""

from pathlib import Path

from agent_factory.workflows.model import Workflow


def to_mermaid(workflow: Workflow) -> str:
    """
    Generate Mermaid syntax from workflow definition.

    Args:
        workflow: Workflow to visualize

    Returns:
        Mermaid diagram syntax
    """
    lines = ["graph TD"]

    # Add start node
    lines.append("    Start([Start])")

    # Add step nodes
    for i, step in enumerate(workflow.steps):
        node_id = f"Step{i}"
        node_label = step.id.replace("_", " ").title()
        lines.append(f"    {node_id}[{node_label}]")

    # Add end node
    lines.append("    End([End])")

    # Add edges
    if workflow.steps:
        lines.append("    Start --> Step0")

        for i in range(len(workflow.steps) - 1):
            lines.append(f"    Step{i} --> Step{i+1}")

        lines.append(f"    Step{len(workflow.steps)-1} --> End")

    return "\n".join(lines)


def to_graphviz(workflow: Workflow) -> str:
    """
    Generate Graphviz DOT syntax from workflow definition.

    Args:
        workflow: Workflow to visualize

    Returns:
        Graphviz DOT syntax
    """
    lines = ["digraph Workflow {"]
    lines.append("    rankdir=LR;")
    lines.append("    node [shape=box];")

    # Add nodes
    for i, step in enumerate(workflow.steps):
        node_id = f"step{i}"
        node_label = step.id.replace("_", " ")
        lines.append(f'    {node_id} [label="{node_label}"];')

    # Add edges
    if workflow.steps:
        lines.append('    start [shape=ellipse, label="Start"];')
        lines.append('    end [shape=ellipse, label="End"];')
        lines.append("    start -> step0;")

        for i in range(len(workflow.steps) - 1):
            lines.append(f"    step{i} -> step{i+1};")

        lines.append(f"    step{len(workflow.steps)-1} -> end;")

    lines.append("}")
    return "\n".join(lines)


def visualize(
    workflow: Workflow,
    format: str = "mermaid",
    output_path: str | None = None,
) -> str:
    """
    Generate visualization and optionally save to file.

    Args:
        workflow: Workflow to visualize
        format: Output format ("mermaid" or "graphviz")
        output_path: Optional path to save file

    Returns:
        Visualization syntax
    """
    if format == "mermaid":
        content = to_mermaid(workflow)
    elif format == "graphviz":
        content = to_graphviz(workflow)
    else:
        raise ValueError(f"Unsupported format: {format}")

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

    return content
