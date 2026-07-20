import asyncio
from langchain_core.messages import HumanMessage
from app.graph.workflow import graph
from langgraph.types import Command

config = {"configurable": {"thread_id": "console"}}

printed_message_ids = set()


async def main():
    state = {"messages": [], "next_node": ""}

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in {"exit", "q"}:
            break

        state["messages"].append(HumanMessage(content=user_input))

        # We start by streaming the input state
        stream_input = state

        while True:
            interrupted = False
            interrupt_payload = None

            # Stream the current execution chunk
            async for namespace, event in graph.astream(
                stream_input, config=config, subgraphs=True
            ):

                # print(f"\n--- RAW EVENT ---\n{event}\n-----------------")
                # 1. Check if the graph hit an interrupt
                for key, value in event.items():
                    if key == "__interrupt__":
                        interrupted = True
                        interrupt_payload = value
                        print(f"\n[Interrupt Hooked]: {interrupt_payload}")
                        continue

                    # 2. Process regular outputs
                    state.update(value)
                    if "messages" in value:
                        last_message = value["messages"][-1]
                        if (
                            last_message.type == "ai"
                            and last_message.id not in printed_message_ids
                        ):
                            printed_message_ids.add(last_message.id)
                            print(f"\nAI: {last_message.content}")

            # If we were interrupted, prompt the user and set up the Command for the next iteration
            if interrupted:
                answer = input("Response to Interrupt: ")
                # Resume execution with the Command primitive.
                # On the next iteration of 'while True', graph.astream will pick up right where it paused.
                interrupted = False
                stream_input = Command(resume=answer)
            else:
                # No interrupts were hit, execution for this turn is fully complete.
                # Break the inner loop and wait for the next "You: " prompt.
                break


if __name__ == "__main__":
    asyncio.run(main())
