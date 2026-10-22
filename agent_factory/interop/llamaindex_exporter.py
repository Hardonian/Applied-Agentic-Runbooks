"""
LlamaIndex Workflow Exporter for Agent Factory.

Compiles Agent Factory agents and workflows into event-driven LlamaIndex
Workflow classes with `@step` decorators and typed events.
"""

from agent_factory.agents.agent import Agent


class LlamaIndexExporter:
    """
    Exports Agent Factory agents and workflows to LlamaIndex Workflows.
    """

    @staticmethod
    def export_agent(agent: Agent) -> str:
        """Export single agent to LlamaIndex event-driven step workflow."""
        clean_name = agent.id.replace("-", "_").title().replace("_", "")
        return f'''"""
LlamaIndex Workflow generated from Agent Factory Agent: {agent.name}
"""

from llama_index.core.workflow import (
    Workflow,
    StartEvent,
    StopEvent,
    step,
    Event,
    Context,
)
from llama_index.llms.openai import OpenAI


class {clean_name}Workflow(Workflow):
    """Event-driven workflow for {agent.name}"""

    @step
    async def process_task(self, ev: StartEvent, ctx: Context) -> StopEvent:
        user_query = getattr(ev, "query", "Hello from LlamaIndex")
        
        # System instructions: {agent.instructions[:120]}...
        llm = OpenAI(model="{agent.model}")
        
        prompt = f"""Instructions: {agent.instructions}
User Query: {{user_query}}"""
        
        # In actual run: response = await llm.acomplete(prompt)
        output = f"[{agent.name} completed: {{user_query}}]"
        
        return StopEvent(result=output)


async def main():
    wf = {clean_name}Workflow(timeout=30.0, verbose=True)
    result = await wf.run(query="Explain quantum computing basics.")
    print("Workflow Output:", result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
'''
