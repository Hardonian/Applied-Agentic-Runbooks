"""
Education Example: Student Support Assistant

This example demonstrates how to create a virtual teaching assistant
for higher education institutions using Agent Factory Platform.

Designed for McGraw Hill Education partnership institutions.
"""

from agent_factory.agents.agent import Agent
from agent_factory.integrations.tools.file_io import read_file
from agent_factory.integrations.tools.web_search import web_search


def create_student_support_agent():
    """Create a student support assistant agent."""
    
    agent = Agent(
        id="student-support-assistant",
        name="Student Support Assistant",
        instructions="""
        You are a helpful virtual teaching assistant for a higher education institution.
        
        Your role is to:
        - Answer student questions about course content, assignments, and deadlines
        - Provide guidance on course materials and resources
        - Help students understand concepts and clarify instructions
        - Direct students to appropriate resources when needed
        - Maintain a supportive and encouraging tone
        
        Always be respectful, patient, and clear in your responses.
        If you don't know something, admit it and suggest where the student can find the answer.
        
        Remember: You're here to support student learning and success.
        """,
        model="gpt-4o",
        tools=[web_search, read_file]
    )
    
    return agent


def main():
    """Run the student support assistant example."""
    
    print("=" * 60)
    print("Student Support Assistant - Education Example")
    print("Agent Factory Platform")
    print("In Partnership with McGraw Hill Education")
    print("=" * 60)
    print()
    
    # Create agent
    agent = create_student_support_agent()
    print("✅ Student Support Assistant created")
    print()
    
    # Example interactions
    examples = [
        "What is the deadline for the research paper?",
        "Can you explain the concept of machine learning?",
        "Where can I find the course syllabus?",
        "I'm struggling with the assignment. Can you help?",
    ]
    
    session_id = "student-12345"
    
    for i, question in enumerate(examples, 1):
        print(f"Student Question {i}: {question}")
        print("-" * 60)
        
        result = agent.run(question, session_id=session_id)
        
        print(f"Assistant Response: {result.output}")
        print(f"Status: {result.status.value}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print()
    
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
