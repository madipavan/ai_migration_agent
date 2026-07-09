
 export async function connectToWebSocket() : Promise<WebSocket>{
    const socket = new WebSocket(
        "ws://127.0.0.1:8000/chat"
    )
    return socket;
 }