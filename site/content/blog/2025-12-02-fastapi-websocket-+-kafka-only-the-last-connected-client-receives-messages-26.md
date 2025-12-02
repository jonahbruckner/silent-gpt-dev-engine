+++
title = "FastAPI WebSocket + Kafka: Only the last connected client receives messages"
date = "2025-12-02T09:21:37.805360"
slug = "fastapi-websocket-+-kafka-only-the-last-connected-client-receives-messages"
description = "When building real-time applications with FastAPI and WebSockets, you might encounter a situation where only the last connected client receives messages. This can be frustrating, especially if you expect all connected clients to receive..."
+++

When building real-time applications with FastAPI and WebSockets, you might encounter a situation where only the last connected client receives messages. This can be frustrating, especially if you expect all connected clients to receive the same messages. In this micro-tutorial, we will explore why this happens and how to resolve it effectively.

## Why This Happens

The issue typically arises from how WebSocket connections are managed and how messages are broadcasted to connected clients. If you are using a global variable or a singleton instance to handle the WebSocket connections, it may lead to overwriting the previous connection with the latest one. Consequently, only the last client that connects will receive the messages.

## Step-by-Step Solution

To ensure that all connected clients receive messages, you need to maintain a list of active WebSocket connections and iterate over that list when sending messages. Here’s how to implement this:

1. **Set up FastAPI and WebSocket routes.**
2. **Maintain a list of connected WebSocket clients.**
3. **Broadcast messages to all connected clients.**

### Full Code Example

Below is a complete example demonstrating how to implement a WebSocket server with FastAPI that broadcasts messages to all connected clients.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List
import asyncio
import json

app = FastAPI()

# List to hold connected WebSocket clients
connected_clients: List[WebSocket] = []

@app.get("/")
async def get():
    return HTMLResponse("""
    <html>
        <head>
            <title>WebSocket Test</title>
        </head>
        <body>
            <h1>WebSocket Test</h1>
            <button onclick="connect()">Connect</button>
            <script>
                let socket;
                function connect() {
                    socket = new WebSocket("ws://localhost:8000/ws");
                    socket.onmessage = function(event) {
                        const message = JSON.parse(event.data);
                        console.log("Received message:", message);
                    };
                }
            </script>
        </body>
    </html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = {"message": data}
            await broadcast(message)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def broadcast(message: dict):
    # Send message to all connected clients
    for client in connected_clients:
        await client.send_text(json.dumps(message))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

### Explanation of the Code

1. **Connected Clients List:** We maintain a list `connected_clients` to store all active WebSocket connections.
2. **WebSocket Endpoint:** The `/ws` endpoint accepts WebSocket connections. When a client connects, it is added to the `connected_clients` list.
3. **Broadcast Function:** The `broadcast` function iterates through all connected clients and sends the message to each one.
4. **Handling Disconnects:** When a client disconnects, it is removed from the `connected_clients` list.

## Example Variation

You might want to enhance the application by adding message types or managing user sessions. Here’s a quick variation that includes a simple message type:

```python
async def broadcast(message: dict):
    for client in connected_clients:
        if message.get("type") == "chat":
            await client.send_text(json.dumps({"type": "chat", "content": message["message"]}))
        elif message.get("type") == "notification":
            await client.send_text(json.dumps({"type": "notification", "content": message["message"]}))
```

In this variation, you can handle different types of messages, allowing for more complex interactions.

## Common Errors & Fixes

1. **Error: Only one client receives messages.**
   - **Fix:** Ensure you are maintaining a list of connected clients and not overwriting the connection variable.

2. **Error: WebSocket connection closes unexpectedly.**
   - **Fix:** Check for exceptions in your WebSocket handling code, especially in the `try-except` block.

3. **Error: Messages not being sent.**
   - **Fix:** Ensure that the `broadcast` function is called correctly and that all clients are still connected.

## Cheat Sheet Summary

- **Maintain a List of Clients:** Use a list to keep track of all connected WebSocket clients.
- **Broadcast Messages:** Iterate through the list of clients and send messages to each one.
- **Handle Disconnects:** Remove clients from the list when they disconnect to avoid sending messages to closed connections.
- **Error Handling:** Implement proper error handling to manage unexpected disconnections or message sending failures.

By following these guidelines, you can successfully implement a FastAPI WebSocket server that broadcasts messages to all connected clients, ensuring a seamless real-time experience.
