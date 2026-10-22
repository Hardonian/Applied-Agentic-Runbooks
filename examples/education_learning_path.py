"""
Education Example: Personalized Learning Path Generator

This example demonstrates how to create a personalized learning path
generator for adaptive learning programs in higher education.

Designed for McGraw Hill Education partnership institutions.
"""

from agent_factory.agents.agent import Agent
from agent_factory.integrations.tools.calculator import calculator
from agent_factory.integrations.tools.web_search import web_search


def create_learning_path_agent():
    """Create a learning path generator agent."""
    
    agent = Agent(
        id="learning-path-generator",
        name="Learning Path Generator",
        instructions="""
        You are a personalized learning path generator for higher education.
        
        Your role is to:
        - Analyze student learning goals and current knowledge
        - Create customized learning paths with recommended resources
        - Adapt paths based on student progress and performance
        - Suggest supplementary materials and activities
        - Track learning objectives and milestones
        
        When creating learning paths, provide:
        - Clear learning objectives
        - Recommended resources (readings, videos, exercises)
        - Estimated time commitments
        - Assessment checkpoints
        - Next steps based on progress
        
        Format your responses as structured learning paths with clear sections.
        """,
        model="gpt-4o",
        tools=[web_search, calculator]
    )
    
    return agent


def main():
    """Run the learning path generator example."""
    
    print("=" * 60)
    print("Personalized Learning Path Generator - Education Example")
    print("Agent Factory Platform")
    print("In Partnership with McGraw Hill Education")
    print("=" * 60)
    print()
    
    # Create agent
    agent = create_learning_path_agent()
    print("✅ Learning Path Generator created")
    print()
    
    # Example: Generate learning path for a student
    student_profile = {
        "name": "Sarah",
        "current_level": "intermediate",
        "learning_goal": "Master Python programming for data science",
        "time_available": "10 hours per week",
        "preferred_learning_style": "hands-on with examples"
    }
    
    prompt = f"""
    Create a personalized learning path for:
    - Student: {student_profile['name']}
    - Current Level: {student_profile['current_level']}
    - Learning Goal: {student_profile['learning_goal']}
    - Time Available: {student_profile['time_available']}
    - Learning Style: {student_profile['preferred_learning_style']}
    
    Please create a 4-week learning path with:
    1. Weekly learning objectives
    2. Recommended resources
    3. Practice exercises
    4. Assessment checkpoints
    """
    
    print("Generating personalized learning path...")
    print("-" * 60)
    
    result = agent.run(prompt)
    
    print(result.output)
    print()
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
