import json
from pathlib import Path

PACK_DIR = Path("notebook-library/packs/pack_0003")
DATA_DIR = PACK_DIR / "data"
OUTPUTS_DIR = PACK_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Create data/prompts.json
sample_prompts = {
    "version": "1.0.0",
    "description": "Benchmark evaluation dataset for prompt versions across common agent workflows",
    "prompts": [
        {
            "id": "prompt_summarization_v1",
            "name": "Financial Document Summarizer (Baseline)",
            "category": "summarization",
            "version": "1.0",
            "system_prompt": "Summarize this financial text for executives. Keep it brief.",
            "test_inputs": [
                "Q3 earnings call transcript: Revenue was up 12% to $4.2B, but cloud infrastructure spend rose 28%. Free cash flow declined by 5% due to accelerated capital expenditures on GPU clusters.",
                "Balance sheet note: Accounts receivable increased by $140M as payment terms extended from net-30 to net-60 for enterprise tier customers."
            ],
            "required_criteria": ["revenue figures", "cost drivers", "cash flow impact"]
        },
        {
            "id": "prompt_summarization_v2",
            "name": "Financial Document Summarizer (Optimized)",
            "category": "summarization",
            "version": "2.0",
            "system_prompt": "You are a Senior Financial Analyst. Summarize the provided document into a structured Executive Brief:\n1. Key Metrics Table (Revenue, Margin, Cash Flow)\n2. Primary Cost & Margin Drivers\n3. Strategic Risk Factors\nConstraints: Maintain strict factual accuracy. Do not extrapolate beyond provided numbers. Maximum 200 words.",
            "test_inputs": [
                "Q3 earnings call transcript: Revenue was up 12% to $4.2B, but cloud infrastructure spend rose 28%. Free cash flow declined by 5% due to accelerated capital expenditures on GPU clusters.",
                "Balance sheet note: Accounts receivable increased by $140M as payment terms extended from net-30 to net-60 for enterprise tier customers."
            ],
            "required_criteria": ["revenue figures", "cost drivers", "cash flow impact", "concise bullet formatting"]
        },
        {
            "id": "prompt_code_gen_v1",
            "name": "API Endpoint Generator (Baseline)",
            "category": "code_generation",
            "version": "1.0",
            "system_prompt": "Write a Python FastAPI endpoint for user authentication.",
            "test_inputs": [
                "Endpoint to authenticate with username and password, return JWT token.",
                "Endpoint to verify refresh token and issue new access token."
            ],
            "required_criteria": ["FastAPI syntax", "JWT handling", "status codes"]
        },
        {
            "id": "prompt_code_gen_v2",
            "name": "API Endpoint Generator (Optimized)",
            "category": "code_generation",
            "version": "2.0",
            "system_prompt": "You are a Principal Backend Engineer. Generate a production-ready FastAPI router endpoint:\n- Use Pydantic v2 schemas for request and response models\n- Implement dependency injection for database session and authentication\n- Include comprehensive error handling with HTTPException (400, 401, 500)\n- Use type hints and docstrings\n- Never hardcode secret keys or credentials.",
            "test_inputs": [
                "Endpoint to authenticate with username and password, return JWT token.",
                "Endpoint to verify refresh token and issue new access token."
            ],
            "required_criteria": ["FastAPI router", "Pydantic v2 schemas", "HTTPException error handling", "no hardcoded secrets"]
        },
        {
            "id": "prompt_support_v1",
            "name": "SaaS Customer Support Bot (Baseline)",
            "category": "customer_support",
            "version": "1.0",
            "system_prompt": "Help users who have billing questions or cancellation requests.",
            "test_inputs": [
                "I was charged twice for my subscription this month. Refund me immediately!",
                "How do I cancel my team account before the annual auto-renewal next week?"
            ],
            "required_criteria": ["polite tone", "billing explanation", "refund instructions"]
        },
        {
            "id": "prompt_support_v2",
            "name": "SaaS Customer Support Bot (Optimized)",
            "category": "customer_support",
            "version": "2.0",
            "system_prompt": "You are an empathetic, professional Tier-1 Customer Support Specialist for a cloud SaaS platform.\nGuidelines:\n1. Acknowledge customer frustration warmly within the first sentence.\n2. Inquire for the Invoice ID or Transaction Date before processing refunds.\n3. Provide step-by-step navigation instructions for billing settings.\n4. If refund is over $250, inform customer of mandatory manager approval within 2 business hours.\n5. Maintain brand tone: Empathetic, clear, and proactive.",
            "test_inputs": [
                "I was charged twice for my subscription this month. Refund me immediately!",
                "How do I cancel my team account before the annual auto-renewal next week?"
            ],
            "required_criteria": ["empathetic acknowledgment", "verification request", "step-by-step guidance", "escalation threshold"]
        }
    ]
}

prompts_file = DATA_DIR / "prompts.json"
with open(prompts_file, "w", encoding="utf-8") as f:
    json.dump(sample_prompts, f, indent=2)
print(f"Created {prompts_file}")
