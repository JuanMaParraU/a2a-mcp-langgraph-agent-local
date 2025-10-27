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
    connect=10.0,  # time to establish connection
    read=120.0,     # time to wait for agent response
    write=10.0,    # time to send request
    pool=5.0       # time to wait for a connection from the pool
)


async def main() -> None:
    async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=BASE_URL,
        )

        final_agent_card_to_use: AgentCard | None = None

        try:
            print(
                f"Fetching public agent card from: {BASE_URL}"
            )
            _public_card = await resolver.get_agent_card()
            print("Fetched public agent card")
            print(_public_card.model_dump_json(indent=2))

            final_agent_card_to_use = _public_card

        except Exception as e:
            print(f"Error fetching public agent card: {e}")
            raise RuntimeError("Failed to fetch public agent card")
        
    #### start communicating with the agent. 

        # 1. Create a ClientConfig (configure as needed)  
        config = ClientConfig(httpx_client=httpx_client,)  
        
        # 2. Initialize the factory with the config  
        factory = ClientFactory(config)  
        
        # 3. Create a client from the agent card  
        client = factory.create(final_agent_card_to_use)  

        print("A2AClient initialized >>>>>>>>>>>>>>>>>>>>")

        #query to the agent
        query = "What are the benefits for woking for the NHS scotland? Provide the tools you used to find the answer."

        message_payload = Message(
            role=Role.user,
            messageId=str(uuid.uuid4()),
            parts=[Part(root=TextPart(text=query))],
        )

        print(f"Sending message: {query}")

        try:
            response = client.send_message(message_payload)
            async for task, event in response:
                #print(task)
                status = event.status
                if status and status.message:
                    for part in status.message.parts:
                        if isinstance(part.root, TextPart):
                            print("Agent reply:", part.root.text)

        except Exception as e:
            print("❌ Error:", e)



if __name__ == "__main__":
    asyncio.run(main())
