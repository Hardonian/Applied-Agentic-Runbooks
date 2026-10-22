"""
Example: Customer Support Bot

Refactored from Agentic_Notebook.ipynb Cell 14
"""

from agent_factory import Agent, function_tool
from agent_factory.core.memory import SQLiteMemoryStore


class KnowledgeBase:
    """Simple knowledge base for FAQ."""
    
    def __init__(self):
        self.kb = {
            'shipping': 'Standard shipping takes 5-7 business days',
            'returns': '30-day return policy for unused items',
            'warranty': '1-year warranty on all products',
            'payment': 'We accept credit cards, PayPal, and Apple Pay',
        }
    
    def search(self, query: str) -> list:
        """Search knowledge base."""
        query_lower = query.lower()
        results = []
        
        for key, value in self.kb.items():
            if query_lower in key or query_lower in value.lower():
                results.append(value)
        
        return results


kb = KnowledgeBase()


@function_tool(name="search_kb")
def search_kb(query: str) -> list:
    """Search the knowledge base for answers."""
    return kb.search(query)


@function_tool(name="create_ticket")
def create_ticket(issue: str) -> dict:
    """Create a support ticket."""
    import uuid
    ticket_id = f"T-{uuid.uuid4().hex[:6].upper()}"
    return {
        'ticket_id': ticket_id,
        'status': 'created',
        'issue': issue,
    }


def main():
    """Create and run customer support bot."""
    # Create support bot with memory
    support_bot = Agent(
        id="support-bot",
        name="Support Bot",
        instructions="""
        You are a helpful customer support bot.
        
        Your responsibilities:
        1. Search the knowledge base first for common questions
        2. Provide clear, friendly answers
        3. Create support tickets for complex issues that you can't resolve
        4. Always be polite and professional
        """,
        tools=[search_kb, create_ticket],
        memory=SQLiteMemoryStore("support_sessions.db"),
    )
    
    # Example conversation
    session_id = "customer-123"
    
    # First question
    result1 = support_bot.run("What's your return policy?", session_id=session_id)
    print("Customer: What's your return policy?")
    print(f"Bot: {result1.output}\n")
    
    # Follow-up question (with memory)
    result2 = support_bot.run("How long does shipping take?", session_id=session_id)
    print("Customer: How long does shipping take?")
    print(f"Bot: {result2.output}\n")
    
    # Complex issue (creates ticket)
    result3 = support_bot.run("My order never arrived", session_id=session_id)
    print("Customer: My order never arrived")
    print(f"Bot: {result3.output}")


if __name__ == "__main__":
    main()
