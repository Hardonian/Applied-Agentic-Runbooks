"""
AutoGen / AG2 Code Exporter for Agent Factory.

Exports Agent Factory agents into AutoGen ConversableAgent and GroupChat configurations.
"""

from agent_factory.agents.agent import Agent


class AutoGenExporter:
    """
    Exports Agent Factory agents and swarms to AutoGen / AG2 code.
    """

    @staticmethod
    def export_agent(agent: Agent) -> str:
        """Export single agent to AutoGen ConversableAgent."""
        system_message = agent.instructions.replace('"', '\\"').replace("\n", "\\n")
        return f'''"""
AutoGen Agent exported from Agent Factory: {agent.name}
"""

import autogen

llm_config = {{
    "config_list": [{{"model": "{agent.model}", "api_key": "YOUR_API_KEY"}}],
    "temperature": 0.7,
}}

{agent.id.replace("-", "_")}_agent = autogen.ConversableAgent(
    name="{agent.name.replace(' ', '_')}",
    system_message="{system_message}",
    llm_config=llm_config,
    human_input_mode="NEVER",
)

user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=2,
    code_execution_config=False,
)

if __name__ == "__main__":
    user_proxy.initiate_chat(
        {agent.id.replace("-", "_")}_agent,
        message="Hello! How can you assist me today?",
    )
'''

    @staticmethod
    def export_group_chat(agents: list[Agent], name: str = "AgentFactoryGroupChat") -> str:
        """Export multi-agent group to AutoGen GroupChat."""
        agent_inits = []
        agent_vars = []

        for a in agents:
            var_name = a.id.replace("-", "_")
            msg = a.instructions.replace('"', '\\"').replace("\n", "\\n")
            code = f"""{var_name} = autogen.ConversableAgent(
    name="{a.name.replace(' ', '_')}",
    system_message="{msg}",
    llm_config=llm_config,
    human_input_mode="NEVER",
)"""
            agent_inits.append(code)
            agent_vars.append(var_name)

        agents_code = "\n\n".join(agent_inits)
        agents_list = ", ".join(agent_vars)

        return f'''"""
AutoGen GroupChat exported from Agent Factory: {name}
"""

import autogen

llm_config = {{
    "config_list": [{{"model": "gpt-4o", "api_key": "YOUR_API_KEY"}}],
    "temperature": 0.7,
}}

# Agent Definitions
{agents_code}

# Group Chat
groupchat = autogen.GroupChat(
    agents=[{agents_list}],
    messages=[],
    max_round=6,
)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

user_proxy = autogen.UserProxyAgent(
    name="Admin",
    human_input_mode="NEVER",
    code_execution_config=False,
)

if __name__ == "__main__":
    user_proxy.initiate_chat(
        manager,
        message="Initiate team collaborative brainstorming on target task.",
    )
'''
