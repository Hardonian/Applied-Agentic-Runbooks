import json
from pathlib import Path

nb_path = Path("Agentic_Notebook.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

src31 = [
    "# ==============================================================================\n",
    "# CELL 15: RESEARCH ASSISTANT - Multi-Agent Template\n",
    "# ==============================================================================\n",
    "try:\n",
    "    from crewai import Agent, Task, Crew, Process\n",
    "except ImportError:\n",
    "    class Process:\n",
    "        sequential = 'sequential'\n",
    "    Agent = CrewAgent\n",
    "    Task = CrewTask\n",
    "    class Crew:\n",
    "        def __init__(self, agents, tasks, process=None):\n",
    "            self.orchestrator = CrewOrchestrator(agents, tasks)\n",
    "        def kickoff(self, inputs):\n",
    "            return self.orchestrator.kickoff(inputs)\n",
    "\n",
    "# Define specialist agents\n",
    "searcher = Agent(\n",
    "    role='Research Searcher',\n",
    "    goal='Find credible sources',\n",
    "    backstory='Expert at finding quality information'\n",
    ")\n",
    "\n",
    "analyst = Agent(\n",
    "    role='Research Analyst',\n",
    "    goal='Extract key insights',\n",
    "    backstory='Skilled data analyst'\n",
    ")\n",
    "\n",
    "writer = Agent(\n",
    "    role='Research Writer',\n",
    "    goal='Create comprehensive reports',\n",
    "    backstory='Professional technical writer'\n",
    ")\n",
    "\n",
    "# Define tasks\n",
    "search_task = Task(\n",
    "    description='Search for information on {topic}',\n",
    "    agent=searcher,\n",
    "    expected_output='Source links and raw factual points'\n",
    ")\n",
    "\n",
    "analyze_task = Task(\n",
    "    description='Analyze findings on {topic}',\n",
    "    agent=analyst,\n",
    "    expected_output='Synthesis of key trends',\n",
    "    context_tasks=[search_task]\n",
    ")\n",
    "\n",
    "write_task = Task(\n",
    "    description='Write comprehensive report on {topic}',\n",
    "    agent=writer,\n",
    "    expected_output='Executive report in markdown',\n",
    "    context_tasks=[search_task, analyze_task]\n",
    ")\n",
    "\n",
    "# Create crew\n",
    "research_crew = Crew(\n",
    "    agents=[searcher, analyst, writer],\n",
    "    tasks=[search_task, analyze_task, write_task],\n",
    "    process=Process.sequential\n",
    ")\n",
    "\n",
    "print('✅ Research Assistant ready!')\n",
    "print('\\nRun: research_crew.kickoff(inputs={\"topic\": \"AI Agents in FinTech\"})')\n"
]

nb["cells"][31]["source"] = src31

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print("Successfully patched Cell 31!")
