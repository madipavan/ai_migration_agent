# from fastapi import FastAPI, WebSocket
# from fastapi.middleware.cors import CORSMiddleware
# from app.graph.workflow import graph

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/health")
# def health():
#     return {"status": "ok"}


# @app.websocket("/chat")
# async def chat(websocket: WebSocket):

#     await websocket.accept()

#     while True:

#         data = await websocket.receive_json()

#         state = {"messages": [{"role": "user", "content": data["message"]}]}

#         async for event in graph.astream(state):
#             if "chat_node" in event:
#                 ai_message = event["chat_node"]["messages"][-1]
#                 await websocket.send_json(ai_message.content)

import asyncio

from langchain_core.messages import HumanMessage
from app.graph.workflow import graph


async def main():

    state = {"messages": [], "next_node": ""}

    while True:

        user_input = input("\nYou: ")

        if user_input.lower() in {"exit", "q"}:
            break

        state["messages"].append(HumanMessage(content=user_input))

        async for event in graph.astream(state):

            for value in event.values():
                state.update(value)

                if "messages" in value:
                    last_message = value["messages"][-1]

                    if last_message.type == "ai":
                        print(f"\nAI: {last_message.content}")


if __name__ == "__main__":
    asyncio.run(main())
