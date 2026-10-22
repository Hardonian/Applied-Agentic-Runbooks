"""
HuggingFace Spaces deployment for Agent Factory.

This file should be placed in the root of your HuggingFace Space.
"""


import gradio as gr

from agent_factory.agents.agent import Agent
from agent_factory.tools.decorator import function_tool


# Create a simple agent
@function_tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! How can I help you today?"

agent = Agent(
    id="hf-demo-agent",
    name="HuggingFace Demo Agent",
    instructions="You are a helpful assistant deployed on HuggingFace Spaces.",
    tools=[greet]
)

def chat(message, history):
    """Chat interface for the agent."""
    try:
        result = agent.run(message)
        response = result.output if hasattr(result, 'output') else str(result)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
demo = gr.ChatInterface(
    fn=chat,
    title="Agent Factory Demo",
    description="AI agent powered by Agent Factory Platform",
    examples=["Hello!", "What can you do?", "Tell me a joke"],
    theme=gr.themes.Soft(),
)

if __name__ == "__main__":
    demo.launch()
