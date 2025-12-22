import uuid
import asyncio
import httpx

from a2a.client.client_factory import ClientFactory
from a2a.client.client import ClientConfig
from a2a.client import A2ACardResolver
from a2a.types import AgentCard, Message, Part, Role, TextPart

BASE_URL = "http://localhost:8001"

# HTTP client timeout configuration
timeout_config = httpx.Timeout(
    connect=10.0,
    read=120.0,
    write=10.0,
    pool=5.0,
)


async def fetch_and_print_agent_card(resolver: A2ACardResolver) -> None:
    """Fetch and print the agent card."""
    try:
        print("\n📋 Fetching agent card...")
        agent_card = await resolver.get_agent_card()
        print("\n" + "=" * 60)
        print("Agent Card:")
        print("=" * 60)
        print(agent_card.model_dump_json(indent=2))
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"❌ Error fetching agent card: {e}\n")


async def main() -> None:
    async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:

        # Initialize agent card resolver
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=BASE_URL)

        try:
            agent_card: AgentCard = await resolver.get_agent_card()
            print(f"✅ Connected to agent at {BASE_URL}")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to connect to agent: {e}")

        # Initialize the A2A client
        config = ClientConfig(httpx_client=httpx_client)
        factory = ClientFactory(config)
        client = factory.create(agent_card)

        print("\n" + "=" * 60)
        print("🤖 Multi-turn A2A Agent ready!")
        print("Type 'quit', 'exit', or 'q' to end.")
        print("Type 'card' to view agent capabilities.")
        print("=" * 60 + "\n")

        # --- Conversation loop ---
        while True:
            try:
                user_input = input("🔎 You: ").strip()

                if user_input.lower() in {"quit", "exit", "q"}:
                    print("\n👋 Goodbye!")
                    break

                if user_input.lower() in {"card", "agent card", "show card"}:
                    await fetch_and_print_agent_card(resolver)
                    continue

                if not user_input:
                    continue

                # Build the message payload
                message = Message(
                    role=Role.user,
                    messageId=str(uuid.uuid4()),
                    parts=[Part(root=TextPart(text=user_input))],
                )

                print("\n🤖 Agent: ", end="", flush=True)

                seen_content = set()
                has_content = False

                try:
                    response = client.send_message(message)

                    async for task, event in response:
                        # --- Check for status messages ---
                        if hasattr(event, "status") and event.status and hasattr(event.status, "message") and event.status.message:
                            for part in event.status.message.parts:
                                if hasattr(part.root, "text"):
                                    content = part.root.text
                                    if content and content not in seen_content:
                                        print(content, end="", flush=True)
                                        seen_content.add(content)
                                        has_content = True

                        # --- Check for singular artifact ---
                        if hasattr(event, "artifact") and event.artifact:
                            artifact = event.artifact
                            for part in artifact.parts:
                                if hasattr(part.root, "text"):
                                    content = part.root.text
                                    if content and content not in seen_content:
                                        print(content, end="", flush=True)
                                        seen_content.add(content)
                                        has_content = True

                        # --- Check for plural artifacts (if present) ---
                        if hasattr(event, "artifacts") and event.artifacts:
                            for artifact in event.artifacts:
                                for part in artifact.parts:
                                    if hasattr(part.root, "text"):
                                        content = part.root.text
                                        if content and content not in seen_content:
                                            print(content, end="", flush=True)
                                            seen_content.add(content)
                                            has_content = True

                    if has_content:
                        print("\n")
                    else:
                        print("(No response)\n")

                except Exception as e:
                    print(f"\n❌ Error sending message: {e}\n")

            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 Goodbye!")
                break

            except Exception as e:
                print(f"\n❌ Unexpected error: {e}\n")

        print("✅ Client closed.")


if __name__ == "__main__":
    asyncio.run(main())
