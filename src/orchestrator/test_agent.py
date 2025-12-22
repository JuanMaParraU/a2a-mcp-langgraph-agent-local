import asyncio
from orchestrator_agent import Orchestrator

async def test_orchestrator():
    agent = Orchestrator()

    # Example queries
    queries = [
        "What is Anthropic?",
        "Search for recent papers on quantum computing",
        "Tell me a joke"
    ]

    for query in queries:
        print(f"\n--- Query: {query} ---")
        result = await agent.invoke(query, context_id="test_thread")
        print("Response:", result["content"])

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
