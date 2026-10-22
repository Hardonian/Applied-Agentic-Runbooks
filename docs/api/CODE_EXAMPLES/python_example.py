"""
Agent Factory Python SDK Example
Complete example demonstrating Agent Factory API usage
"""

import os
import time

from agentfactory import AgentFactory, APIError, RateLimitError

# Initialize client
api_key = os.getenv("AGENTFACTORY_API_KEY", "your_api_key")
client = AgentFactory(api_key=api_key)

def example_create_agent():
    """Example: Create a new agent"""
    try:
        agent = client.agents.create(
            name="Customer Support Bot",
            blueprint_id="support_bot_blueprint",
            knowledge_base_id="kb_123",
            description="AI-powered customer support agent"
        )
        print(f"Agent created: {agent.id}")
        return agent
    except APIError as e:
        print(f"Error creating agent: {e.message}")
        return None

def example_get_agent(agent_id):
    """Example: Get an agent"""
    try:
        agent = client.agents.get(agent_id)
        print(f"Agent: {agent.name}")
        return agent
    except APIError as e:
        print(f"Error getting agent: {e.message}")
        return None

def example_chat_with_agent(agent_id, message):
    """Example: Chat with an agent"""
    try:
        agent = client.agents.get(agent_id)
        conversation = agent.conversations.create()
        response = conversation.send_message(message)
        print(f"Agent response: {response.text}")
        return response
    except APIError as e:
        print(f"Error chatting with agent: {e.message}")
        return None

def example_create_knowledge_base():
    """Example: Create a knowledge base"""
    try:
        kb = client.knowledge_bases.create(
            name="Product Knowledge Base",
            description="Knowledge base for product information"
        )
        print(f"Knowledge base created: {kb.id}")
        
        # Add documents
        kb.documents.add(
            content="Product X is our flagship product...",
            metadata={"title": "Product X Overview", "category": "products"}
        )
        print("Document added to knowledge base")
        return kb
    except APIError as e:
        print(f"Error creating knowledge base: {e.message}")
        return None

def example_query_knowledge_base(kb_id, query):
    """Example: Query a knowledge base"""
    try:
        kb = client.knowledge_bases.get(kb_id)
        results = kb.query(query, limit=5)
        print(f"Found {len(results)} results:")
        for result in results:
            print(f"- {result.title}: {result.snippet}")
        return results
    except APIError as e:
        print(f"Error querying knowledge base: {e.message}")
        return None

def example_create_webhook():
    """Example: Create a webhook"""
    try:
        webhook = client.webhooks.create(
            name="My Webhook",
            url="https://example.com/webhooks/agentfactory",
            events=["agent.created", "conversation.message"],
            secret="your_webhook_secret"
        )
        print(f"Webhook created: {webhook.id}")
        return webhook
    except APIError as e:
        print(f"Error creating webhook: {e.message}")
        return None

def example_list_agents():
    """Example: List all agents"""
    try:
        agents = client.agents.list(limit=10)
        print(f"Found {len(agents)} agents:")
        for agent in agents:
            print(f"- {agent.name} ({agent.id})")
        return agents
    except APIError as e:
        print(f"Error listing agents: {e.message}")
        return []

def example_rate_limit_handling():
    """Example: Handle rate limits with retry"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            agents = client.agents.list()
            return agents
        except RateLimitError as e:
            retry_count += 1
            if retry_count >= max_retries:
                print("Max retries reached")
                raise
            
            wait_time = e.retry_after if hasattr(e, 'retry_after') else 60
            print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except APIError as e:
            print(f"API Error: {e.message}")
            raise

def example_error_handling():
    """Example: Comprehensive error handling"""
    try:
        agent = client.agents.get("invalid_agent_id")
    except APIError as e:
        if e.status_code == 404:
            print("Agent not found")
        elif e.status_code == 401:
            print("Authentication failed")
        elif e.status_code == 429:
            print("Rate limit exceeded")
        else:
            print(f"API Error: {e.message} (Status: {e.status_code})")

def main():
    """Main example function"""
    print("Agent Factory Python SDK Examples")
    print("=" * 40)
    
    # Example 1: Create agent
    print("\n1. Creating agent...")
    agent = example_create_agent()
    
    if agent:
        # Example 2: Get agent
        print("\n2. Getting agent...")
        example_get_agent(agent.id)
        
        # Example 3: Chat with agent
        print("\n3. Chatting with agent...")
        example_chat_with_agent(agent.id, "Hello, how can you help me?")
    
    # Example 4: Create knowledge base
    print("\n4. Creating knowledge base...")
    kb = example_create_knowledge_base()
    
    if kb:
        # Example 5: Query knowledge base
        print("\n5. Querying knowledge base...")
        example_query_knowledge_base(kb.id, "What is Product X?")
    
    # Example 6: Create webhook
    print("\n6. Creating webhook...")
    example_create_webhook()
    
    # Example 7: List agents
    print("\n7. Listing agents...")
    example_list_agents()
    
    # Example 8: Rate limit handling
    print("\n8. Rate limit handling...")
    example_rate_limit_handling()
    
    # Example 9: Error handling
    print("\n9. Error handling...")
    example_error_handling()
    
    print("\n" + "=" * 40)
    print("Examples completed!")

if __name__ == "__main__":
    main()
