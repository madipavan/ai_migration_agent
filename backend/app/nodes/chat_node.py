from app.state import AgentState
from app.core.get_llm import get_llm
from langchain_core.messages import AIMessage, SystemMessage

llm = get_llm()


SYSTEM_PROMPT = """
You are Codeshift AI.

You are a software migration expert.
Help the user with programming, migration, debugging, and architecture questions.
If the user is just chatting,only answer if user is chating in context of migration if not reply with friendly message that i am only agent that only have context of code shift of migration of project naturally and in professional way.
"""


async def chat_node(state: AgentState):
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = await llm.ainvoke(messages)

    return {"messages": [AIMessage(content=response.content)]}
