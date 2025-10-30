import uuid
import asyncio
import httpx
from a2a.client.client_factory import ClientFactory
from a2a.client.client import ClientConfig
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    Message,
    Part,
    Role,
    TextPart,
)

BASE_URL = "http://localhost:9998"

# Set timeout values
timeout_config = httpx.Timeout(
    connect=10.0,
    read=120.0,
    write=10.0,
    pool=5.0
)


async def fetch_and_print_agent_card(resolver: A2ACardResolver) -> None:
    """Fetch and display the agent card."""
    try:
        print("\n📋 Fetching agent card...")
        agent_card = await resolver.get_agent_card()
        print("\n" + "="*60)
        print("Agent Card:")
        print("="*60)
        print(agent_card.model_dump_json(indent=2))
        print("="*60 + "\n")
    except Exception as e:
        print(f"❌ Error fetching agent card: {e}\n")


async def main() -> None:
    async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=BASE_URL,
        )

        final_agent_card_to_use: AgentCard | None = None

        # Fetch agent card silently for client initialization
        try:
            _public_card = await resolver.get_agent_card()
            final_agent_card_to_use = _public_card
            print(f"✅ Connected to agent at {BASE_URL}")
        except Exception as e:
            print(f"❌ Error connecting to agent: {e}")
            raise RuntimeError("Failed to connect to agent")
        
        # Initialize the A2A client
        config = ClientConfig(httpx_client=httpx_client)
        factory = ClientFactory(config)
        client = factory.create(final_agent_card_to_use)

        print("\n" + "="*60)
        print("🤖 Multi-turn A2A Agent ready!")
        print("Type 'quit', 'exit', or 'q' to end the conversation.")
        print("Type 'card' or 'agent card' to view the agent's capabilities.")
        print("="*60 + "\n")

        # Multi-turn conversation loop
        while True:
            try:
                user_input = input("🔎 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() in ['card', 'agent card', 'show card']:
                    await fetch_and_print_agent_card(resolver)
                    continue
                
                if not user_input:
                    continue
                
                message_payload = Message(
                    role=Role.user,
                    messageId=str(uuid.uuid4()),
                    parts=[Part(root=TextPart(text=user_input))],
                )

                print("\n🤖 Agent: ", end="", flush=True)

                try:
                    response = client.send_message(message_payload)
                    
                    seen_content = set()
                    has_content = False
                    
                    async for task, event in response:
                        status = event.status
                        if status and status.message:
                            for part in status.message.parts:
                                if isinstance(part.root, TextPart):
                                    content = part.root.text
                                    
                                    if content not in seen_content:
                                        print(content, end="", flush=True)  # ✅ Just this
                                        seen_content.add(content)
                                        has_content = True
                    
                    if has_content:
                        print("\n")  # Only ONE newline at the very end
                    else:
                        print("(No response)\n")

                except Exception as e:
                    print(f"\n❌ Error sending message: {e}\n")
                    continue

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}\n")
                continue

        print("✅ Client closed.")


if __name__ == "__main__":
    asyncio.run(main())
