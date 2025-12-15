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
        logger.debug(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.debug(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except (WebSocketDisconnect, ConnectionError) as e:
                # Remove stale connections on expected disconnect errors
                logger.debug(f"WebSocket client disconnected: {type(e).__name__}")
                self.disconnect(connection)
            except Exception as e:
                # Log unexpected errors for debugging
                logger.error(f"WebSocket broadcast error: {type(e).__name__}: {str(e)}", exc_info=True)
                self.disconnect(connection)


manager = WSManager()
