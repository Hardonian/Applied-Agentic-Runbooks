"""
Streamlit Demo UI for Agent Factory Platform.

Features:
- Agent playground (input/output)
- Workflow visualizer (Mermaid)
- Blueprint browser
- Prompt log viewer
"""

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Agent Factory Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "agent_results" not in st.session_state:
    st.session_state.agent_results = []
if "selected_blueprint" not in st.session_state:
    st.session_state.selected_blueprint = None


def load_blueprints() -> list:
    """Load available blueprints."""
    try:
        from agent_factory.registry.local_registry import LocalRegistry
        registry = LocalRegistry()
        blueprints = registry.list_blueprints()
        return [registry.get_blueprint(bp_id) for bp_id in blueprints if registry.get_blueprint(bp_id)]
    except Exception as e:
        st.error(f"Error loading blueprints: {e}")
        return []


def run_agent(agent_id: str, input_text: str) -> dict[str, Any] | None:
    """Run an agent with given input."""
    try:
        from agent_factory.agents.agent import Agent
        from agent_factory.registry.local_registry import LocalRegistry
        
        registry = LocalRegistry()
        agent_config = registry.get_agent(agent_id)
        
        if not agent_config:
            return {"error": f"Agent {agent_id} not found"}
        
        # Create agent instance
        agent = Agent(
            id=agent_config.get("id", agent_id),
            name=agent_config.get("name", agent_id),
            instructions=agent_config.get("instructions", ""),
            tools=agent_config.get("tools", [])
        )
        
        # Run agent
        result = agent.run(input_text)
        
        return {
            "agent_id": agent_id,
            "input": input_text,
            "output": result.output if hasattr(result, 'output') else str(result),
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
    except Exception as e:
        return {
            "agent_id": agent_id,
            "input": input_text,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False
        }


def get_workflow_mermaid(workflow_id: str) -> str | None:
    """Generate Mermaid diagram for a workflow."""
    try:
        from agent_factory.registry.local_registry import LocalRegistry
        
        registry = LocalRegistry()
        workflow = registry.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        # Generate simple Mermaid diagram
        mermaid = "graph TD\n"
        
        # Add nodes
        if hasattr(workflow, 'steps'):
            for i, step in enumerate(workflow.steps):
                step_id = step.get('id', f'step_{i}')
                step_type = step.get('type', 'agent')
                mermaid += f"    {step_id}[{step_type}: {step_id}]\n"
        
        # Add edges
        if hasattr(workflow, 'steps'):
            for i, step in enumerate(workflow.steps):
                step_id = step.get('id', f'step_{i}')
                if 'next' in step:
                    next_id = step['next']
                    mermaid += f"    {step_id} --> {next_id}\n"
        
        return mermaid
    except Exception as e:
        st.error(f"Error generating workflow diagram: {e}")
        return None


def load_prompt_logs() -> list:
    """Load prompt logs (placeholder - implement with actual log storage)."""
    # This would connect to actual prompt log storage
    return []


# Sidebar
with st.sidebar:
    st.title("🤖 Agent Factory")
    st.markdown("**Demo UI**")
    
    page = st.radio(
        "Navigation",
        ["Agent Playground", "Workflow Visualizer", "Blueprint Browser", "Prompt Logs"],
        label_visibility="collapsed"
    )


# Main content
if page == "Agent Playground":
    st.title("🎮 Agent Playground")
    st.markdown("Test agents interactively")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Input")
        agent_id = st.text_input("Agent ID", value="research-assistant")
        input_text = st.text_area("Input", height=200, placeholder="Enter your message here...")
        
        if st.button("Run Agent", type="primary"):
            with st.spinner("Running agent..."):
                result = run_agent(agent_id, input_text)
                if result:
                    st.session_state.agent_results.append(result)
    
    with col2:
        st.subheader("Output")
        if st.session_state.agent_results:
            latest = st.session_state.agent_results[-1]
            if latest.get("success"):
                st.success("✅ Success")
                st.text_area("Response", value=latest.get("output", ""), height=200, disabled=True)
                st.caption(f"Timestamp: {latest.get('timestamp', '')}")
            else:
                st.error("❌ Error")
                st.text_area("Error", value=latest.get("error", ""), height=200, disabled=True)
        else:
            st.info("Run an agent to see results here")
    
    # Results history
    if st.session_state.agent_results:
        st.subheader("History")
        df = pd.DataFrame(st.session_state.agent_results)
        st.dataframe(df[["agent_id", "input", "timestamp", "success"]], use_container_width=True)
        
        if st.button("Clear History"):
            st.session_state.agent_results = []
            st.rerun()


elif page == "Workflow Visualizer":
    st.title("📊 Workflow Visualizer")
    st.markdown("Visualize agent workflows")
    
    workflow_id = st.text_input("Workflow ID", value="research-workflow")
    
    if st.button("Load Workflow"):
        mermaid_code = get_workflow_mermaid(workflow_id)
        
        if mermaid_code:
            st.subheader("Workflow Diagram")
            st.markdown(f"```mermaid\n{mermaid_code}\n```")
            
            # Also show JSON representation
            with st.expander("Workflow JSON"):
                try:
                    from agent_factory.registry.local_registry import LocalRegistry
                    registry = LocalRegistry()
                    workflow = registry.get_workflow(workflow_id)
                    st.json(workflow if workflow else {})
                except Exception as e:
                    st.error(f"Error loading workflow: {e}")
        else:
            st.warning(f"Workflow '{workflow_id}' not found")
    
    # Example workflow
    st.subheader("Example Workflow")
    example_mermaid = """graph TD
    A[Start] --> B[Research Agent]
    B --> C[Analysis Agent]
    C --> D[Report Generator]
    D --> E[End]
    """
    st.markdown(f"```mermaid\n{example_mermaid}\n```")


elif page == "Blueprint Browser":
    st.title("📦 Blueprint Browser")
    st.markdown("Browse and explore available blueprints")
    
    blueprints = load_blueprints()
    
    if blueprints:
        blueprint_names = [bp.id if hasattr(bp, 'id') else str(bp) for bp in blueprints]
        selected = st.selectbox("Select Blueprint", blueprint_names)
        
        if selected:
            selected_bp = next((bp for bp in blueprints if (hasattr(bp, 'id') and bp.id == selected) or str(bp) == selected), None)
            
            if selected_bp:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("Blueprint Details")
                    if hasattr(selected_bp, 'name'):
                        st.write(f"**Name:** {selected_bp.name}")
                    if hasattr(selected_bp, 'version'):
                        st.write(f"**Version:** {selected_bp.version}")
                    if hasattr(selected_bp, 'description'):
                        st.write(f"**Description:** {selected_bp.description}")
                    if hasattr(selected_bp, 'author'):
                        st.write(f"**Author:** {selected_bp.author}")
                    if hasattr(selected_bp, 'category'):
                        st.write(f"**Category:** {selected_bp.category}")
                
                with col2:
                    st.subheader("Configuration")
                    try:
                        bp_dict = {
                            "id": getattr(selected_bp, 'id', 'unknown'),
                            "name": getattr(selected_bp, 'name', 'unknown'),
                            "version": getattr(selected_bp, 'version', 'unknown'),
                        }
                        st.json(bp_dict)
                    except Exception as e:
                        st.error(f"Error displaying blueprint: {e}")
                
                if st.button("Install Blueprint"):
                    st.success(f"Blueprint '{selected}' installed!")
    else:
        st.info("No blueprints found. Install blueprints using: `agent-factory blueprint install <blueprint-id>`")


elif page == "Prompt Logs":
    st.title("📝 Prompt Log Viewer")
    st.markdown("View and analyze prompt execution logs")
    
    logs = load_prompt_logs()
    
    if logs:
        df = pd.DataFrame(logs)
        st.dataframe(df, use_container_width=True)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            date_filter = st.date_input("Filter by Date")
        with col2:
            agent_filter = st.selectbox("Filter by Agent", ["All"] + list(df.get("agent_id", []).unique()))
    else:
        st.info("No prompt logs available. Logs will appear here as agents are executed.")
        
        # Example log structure
        with st.expander("Example Log Structure"):
            example_log = {
                "timestamp": datetime.now().isoformat(),
                "agent_id": "research-assistant",
                "input": "What is AI?",
                "output": "AI is...",
                "tokens_used": 150,
                "latency_ms": 1200
            }
            st.json(example_log)


# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Agent Factory Platform Demo UI | 
        <a href='https://docs.agentfactory.io'>Documentation</a> | 
        <a href='https://github.com/agentfactory/platform'>GitHub</a></p>
    </div>
    """,
    unsafe_allow_html=True
)
