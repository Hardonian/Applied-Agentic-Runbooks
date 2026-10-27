"""
CrewAI Exporter for Agent Factory.

Exports Agent Factory Agents and multi-agent workflows into native CrewAI
Agent, Task, and Crew configurations.
"""

from agent_factory.agents.agent import Agent


class CrewAIExporter:
    """
    Exports Agent Factory agents and workflows to CrewAI code.
    """

    @staticmethod
    def export_agent(agent: Agent) -> str:
        """Export single agent to CrewAI agent format."""
        backstory = agent.instructions.replace("\n", " ").replace('"', '\\"')
        role = agent.name.replace('"', '\\"')
        goal = f"Execute tasks effectively using {agent.name} capabilities."

        return f'''"""
CrewAI Agent exported from Agent Factory: {agent.name}
"""

from crewai import Agent, Task, Crew, Process

# Define CrewAI Agent
{agent.id.replace("-", "_")}_agent = Agent(
    role="{role}",
    goal="{goal}",
    backstory="""{backstory}""",
    verbose=True,
    memory=True,
    allow_delegation=False,
)

# Example Task
task = Task(
    description="Analyze and process user query with precision.",
    expected_output="Detailed summary report.",
    agent={agent.id.replace("-", "_")}_agent,
)

crew = Crew(
    agents=[{agent.id.replace("-", "_")}_agent],
    tasks=[task],
    process=Process.sequential,
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("Crew Output:", result)
'''

    @staticmethod
    def export_swarm(agents: list[Agent], name: str = "AgentFactoryCrew") -> str:
        """Export multi-agent swarm to CrewAI Crew with tasks."""
        agent_defs = []
        task_defs = []
        agent_names = []
        task_names = []

        for idx, a in enumerate(agents):
            clean_id = a.id.replace("-", "_")
            role = a.name.replace('"', '\\"')
            backstory = a.instructions.replace("\n", " ").replace('"', '\\"')

            agent_code = f'''{clean_id}_agent = Agent(
    role="{role}",
    goal="Collaborate and excel in {role} domain.",
    backstory="""{backstory}""",
    verbose=True,
)'''
            agent_defs.append(agent_code)
            agent_names.append(f"{clean_id}_agent")

            task_code = f"""task_{clean_id} = Task(
    description="Perform {role} contribution for the shared crew objective.",
    expected_output="Domain analysis output.",
    agent={clean_id}_agent,
)"""
            task_defs.append(task_code)
            task_names.append(f"task_{clean_id}")

        agents_block = "\n\n".join(agent_defs)
        tasks_block = "\n\n".join(task_defs)
        agents_list_str = ", ".join(agent_names)
        tasks_list_str = ", ".join(task_names)

        return f'''"""
CrewAI Multi-Agent Crew exported from Agent Factory: {name}
"""

from crewai import Agent, Task, Crew, Process

# Agents
{agents_block}

# Tasks
{tasks_block}

# Crew
{name.replace("-", "_")}_crew = Crew(
    agents=[{agents_list_str}],
    tasks=[{tasks_list_str}],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    result = {name.replace("-", "_")}_crew.kickoff()
    print("Crew Output:", result)
'''
