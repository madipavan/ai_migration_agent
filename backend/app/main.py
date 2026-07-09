from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()

    await websocket.send_json(
        {"type": "assistant", "message": "👋 Hi, I'm CodeShift AI"}
    )

    while True:
        data = await websocket.receive_json()
        print(data)
        user_message = data["message"]

        await websocket.send_json(
            {"type": "assistant", "message": f"You said: {user_message}"}
        )
