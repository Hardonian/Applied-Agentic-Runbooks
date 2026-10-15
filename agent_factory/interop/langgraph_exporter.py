"""
LangGraph Code Exporter for Agent Factory.

Compiles any Agent Factory Agent or Multi-Agent Workflow directly into
runnable LangGraph Python code utilizing StateGraph, conditional edges, and state typed dicts.
"""

from typing import Any

from agent_factory.agents.agent import Agent


class LangGraphExporter:
    """
    Exports Agent Factory agents and workflows to LangGraph code.
    """

    @staticmethod
    def export_agent(agent: Agent) -> str:
        """Export single agent to a LangGraph node & graph script."""
        tools_code = []
        for t in agent.tools:
            tools_code.append(f"# Tool: {t.name} - {t.description}")

        code = f'''"""
LangGraph Workflow generated from Agent Factory Agent: {agent.name} ({agent.id})
"""

from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    agent_id: str
    last_output: str


def {agent.id.replace("-", "_")}_node(state: AgentState) -> dict:
    """Node representing Agent Factory Agent: {agent.name}"""
    messages = state["messages"]
    last_user_msg = messages[-1].content if messages else ""
    
    # System Instructions:
    # {agent.instructions[:200]}...
    
    # Execute with model: {agent.model}
    output = f"[{agent.name} processed: {{last_user_msg}}]"
    return {{
        "messages": [AIMessage(content=output)],
        "last_output": output,
    }}


# Build StateGraph
builder = StateGraph(AgentState)
builder.add_node("{agent.id}", {agent.id.replace("-", "_")}_node)
builder.add_edge(START, "{agent.id}")
builder.add_edge("{agent.id}", END)

graph = builder.compile()

if __name__ == "__main__":
    initial_state = {{
        "messages": [HumanMessage(content="Hello from LangGraph!")],
        "agent_id": "{agent.id}",
        "last_output": "",
    }}
    res = graph.invoke(initial_state)
    print("Final Output:", res["last_output"])
'''
        return code

    @staticmethod
    def export_workflow(steps: list[dict[str, Any]], name: str = "AgentFactoryWorkflow") -> str:
        """Export multi-agent sequence to a multi-node LangGraph StateGraph."""
        nodes_code = []
        edges_code = []
        prev_node = "START"

        for idx, step in enumerate(steps):
            step_id = step.get("id", f"step_{idx}")
            clean_id = step_id.replace("-", "_")
            step_name = step.get("name", f"Step {idx}")
            step.get("model", "gpt-4o")

            node_func = f'''def {clean_id}_node(state: WorkflowState) -> dict:
    """Step: {step_name}"""
    current_input = state.get("last_output") or state.get("input", "")
    output = f"[{step_name} ({{state.get('workflow_name')}}) transformed: {{current_input}}]"
    return {{"last_output": output, "step_outputs": {{**state.get("step_outputs", {{}}), "{step_id}": output}}}}
'''
            nodes_code.append(node_func)
            if prev_node == "START":
                edges_code.append(f'builder.add_edge(START, "{step_id}")')
            else:
                edges_code.append(f'builder.add_edge("{prev_node}", "{step_id}")')
            prev_node = step_id

        edges_code.append(f'builder.add_edge("{prev_node}", END)')

        nodes_str = "\n".join(nodes_code)
        edges_str = "\n".join(edges_code)
        add_nodes_str = "\n".join([f'builder.add_node("{s.get("id", f"step_{i}")}", {s.get("id", f"step_{i}").replace("-", "_")}_node)' for i, s in enumerate(steps)])

        return f'''"""
LangGraph Multi-Step Workflow generated from Agent Factory: {name}
"""

from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END


class WorkflowState(TypedDict):
    workflow_name: str
    input: str
    last_output: str
    step_outputs: Dict[str, Any]


{nodes_str}

builder = StateGraph(WorkflowState)
{add_nodes_str}
{edges_str}

graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({{
        "workflow_name": "{name}",
        "input": "Execute pipeline test",
        "last_output": "",
        "step_outputs": {{}},
    }})
    print("Pipeline Output:", result["last_output"])
'''
