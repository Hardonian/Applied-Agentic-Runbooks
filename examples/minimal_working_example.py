"""
Minimal working example demonstrating agent → tool → workflow → result roundtrip.

This example shows:
1. Creating a tool
2. Creating an agent with the tool
3. Running the agent
4. Creating a workflow with the agent
5. Running the workflow
"""

from agent_factory import Agent, Workflow, WorkflowStep, function_tool


# Step 1: Create a minimal tool
@function_tool(
    name="greet",
    description="Greet someone by name"
)
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}! Nice to meet you."


# Step 2: Create a minimal agent
agent = Agent(
    id="greeting-agent",
    name="Greeting Agent",
    instructions="You are a friendly assistant that greets people.",
    tools=[greet],
    model="gpt-4o",  # Will fallback to mock if API key not set
)


# Step 3: Run the agent directly
print("=" * 60)
print("Running agent directly:")
print("=" * 60)
result = agent.run("Please greet Alice")
print(f"Output: {result.output}")
print(f"Status: {result.status}")
print(f"Execution time: {result.execution_time:.2f}s")
print()


# Step 4: Create a minimal workflow
workflow = Workflow(
    id="greeting-workflow",
    name="Greeting Workflow",
    steps=[
        WorkflowStep(
            id="greet-step",
            agent_id="greeting-agent",
            input_mapping={"input": "$trigger.input"},
        ),
    ],
    agents_registry={"greeting-agent": agent},
)


# Step 5: Run the workflow
print("=" * 60)
print("Running workflow:")
print("=" * 60)
workflow_result = workflow.execute({"input": "Please greet Bob"})
print(f"Success: {workflow_result.success}")
print(f"Steps executed: {workflow_result.steps_executed}")
print(f"Output: {workflow_result.output}")
print(f"Execution time: {workflow_result.execution_time:.2f}s")
print()


# Step 6: Demonstrate tool execution directly
print("=" * 60)
print("Running tool directly:")
print("=" * 60)
tool_result = greet(name="Charlie")
print(f"Tool result: {tool_result}")
print()


print("=" * 60)
print("Example completed successfully!")
print("=" * 60)
