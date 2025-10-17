import logging
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from a2a_3_agent import langG_agent #import the actual agent class (langGraph)
"""
This is the executor class which is wrapped by the startlette app/server. It call imports
the actual agent class from LangGraph (or similar). It always needs to:
1) Initialise the agent
2) Have an *execute* function which is called every time there's a request from the agent
3) A *cancel* function to calcel/stop a task based on an ID,
"""


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LangGraphAgentExecutor(AgentExecutor):
    """Langraph simple agent executor"""
    def __init__(self):
        self.agent = langG_agent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        ### managing inputs
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")
        ### update the tasks for the agent
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()
        ### using the input generate a query for the agent
        query = context.get_user_input()
        try:
            async for item in self.agent.stream(query, context.context_id):
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]
                parts = [Part(root=TextPart(text=item["content"]))]

                if not is_task_complete and not require_user_input:
                    await updater.update_status(
                        TaskState.working,
                        message=updater.new_agent_message(parts),
                    )
                elif require_user_input:
                    await updater.update_status(
                        TaskState.input_required,
                        message=updater.new_agent_message(parts),
                    )
                    break
                else:
                    await updater.add_artifact(
                        parts,
                        name="search result",
                    )
                    await updater.complete()
                    break
        
        except Exception as e:
            logger.error(f"An error occurred while streaming the response: {e}")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())