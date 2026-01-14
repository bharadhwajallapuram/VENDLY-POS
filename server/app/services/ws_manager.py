import json
import logging
from typing import List

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WSManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WS] Client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        print(
            f"[WS] Broadcasting to {len(self.active_connections)} clients: {message.get('event', 'unknown')}"
        )
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
                print(f"[WS] Message sent successfully")
            except (WebSocketDisconnect, ConnectionError) as e:
                print(f"[WS] Client disconnected during broadcast: {type(e).__name__}")
                self.disconnect(connection)
            except Exception as e:
                print(f"[WS] Broadcast error: {type(e).__name__}: {str(e)}")
                self.disconnect(connection)


manager = WSManager()
