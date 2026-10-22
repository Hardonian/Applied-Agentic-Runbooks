"""
Example: Multi-Agent System with Handoffs

Refactored from Agentic_Notebook.ipynb Cell 5
"""

from agent_factory import Agent, Handoff, function_tool

# Create specialist agents
data_analyst = Agent(
    id="data-analyst",
    name="Data Analyst",
    instructions="You analyze data and provide statistical insights.",
)

content_writer = Agent(
    id="content-writer",
    name="Content Writer",
    instructions="You create engaging, well-structured content.",
)

technical_expert = Agent(
    id="technical-expert",
    name="Technical Expert",
    instructions="You provide deep technical knowledge and code examples.",
)


# Delegation tools
@function_tool(name="delegate_to_analyst")
def delegate_to_analyst() -> Handoff:
    """Delegate to data analyst for analytical tasks."""
    return Handoff(to=data_analyst)


@function_tool(name="delegate_to_writer")
def delegate_to_writer() -> Handoff:
    """Delegate to content writer for writing tasks."""
    return Handoff(to=content_writer)


@function_tool(name="delegate_to_technical")
def delegate_to_technical() -> Handoff:
    """Delegate to technical expert for technical questions."""
    return Handoff(to=technical_expert)


# Coordinator agent
coordinator = Agent(
    id="coordinator",
    name="Coordinator",
    instructions="""
    You are an intelligent coordinator.
    
    Routing rules:
    - Data/analytics questions → delegate_to_analyst
    - Writing/content tasks → delegate_to_writer
    - Technical/code questions → delegate_to_technical
    """,
    tools=[delegate_to_analyst, delegate_to_writer, delegate_to_technical],
)


def main():
    """Run the multi-agent system."""
    # Example: Analyze sales data
    result = coordinator.run("Analyze sales: Q1=$100k, Q2=$150k")
    
    print(f"Output: {result.output}")
    print(f"Status: {result.status}")


if __name__ == "__main__":
    main()
