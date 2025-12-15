"""
Vendly POS - WebSocket Manager
================================
Real-time event broadcasting for inventory, sales, and system events
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WSEventType(str, PyEnum):
    """WebSocket event types"""

    SALE_CREATED = "sale_created"
    SALE_COMPLETED = "sale_completed"
    SALE_VOIDED = "sale_voided"
    INVENTORY_UPDATED = "inventory_updated"
    INVENTORY_LOW_STOCK = "inventory_low_stock"
    INVENTORY_OUT_OF_STOCK = "inventory_out_of_stock"
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    USER_ACTIVITY = "user_activity"
    SYSTEM_NOTIFICATION = "system_notification"


class WSMessage:
    """WebSocket message structure"""

    def __init__(
        self,
        event_type: WSEventType,
        data: Dict[str, Any],
        timestamp: Optional[str] = None,
    ):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(
            {
                "type": self.event_type.value,
                "data": self.data,
                "timestamp": self.timestamp,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class InventoryUpdateData:
    """Inventory update event data"""

    def __init__(
        self,
        product_id: int,
        product_name: str,
        previous_qty: int,
        new_qty: int,
        reason: str,  # 'sale', 'adjustment', 'restock', 'return'
        min_qty: int = 0,
        warehouse_id: Optional[int] = None,
    ):
        self.product_id = product_id
        self.product_name = product_name
        self.previous_qty = previous_qty
        self.new_qty = new_qty
        self.reason = reason
        self.min_qty = min_qty
        self.warehouse_id = warehouse_id
        self.change = new_qty - previous_qty
        self.is_low_stock = new_qty <= min_qty and new_qty > 0
        self.is_out_of_stock = new_qty == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "previous_qty": self.previous_qty,
            "new_qty": self.new_qty,
            "change": self.change,
            "reason": self.reason,
            "min_qty": self.min_qty,
            "is_low_stock": self.is_low_stock,
            "is_out_of_stock": self.is_out_of_stock,
            "warehouse_id": self.warehouse_id,
            "updated_at": datetime.utcnow().isoformat(),
        }


class ConnectionManager:
    """Manage WebSocket connections and broadcast events"""

    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store broadcast connections (no auth required)
        self.broadcast_connections: Set[WebSocket] = set()
        # Event hooks for custom handlers
        self.event_hooks: Dict[WSEventType, list] = {
            event_type: [] for event_type in WSEventType
        }

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None):
        """Accept and register a WebSocket connection"""
        await websocket.accept()

        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            logger.info(
                f"User {user_id} connected. Total: {len(self.active_connections[user_id])}"
            )
        else:
            self.broadcast_connections.add(websocket)
            logger.info(
                f"Broadcast connection established. Total: {len(self.broadcast_connections)}"
            )

    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None):
        """Unregister a WebSocket connection"""
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected")
        else:
            self.broadcast_connections.discard(websocket)
            logger.info(
                f"Broadcast connection closed. Remaining: {len(self.broadcast_connections)}"
            )

    async def broadcast(self, message: WSMessage, user_id: Optional[int] = None):
        """
        Broadcast message to all connections or specific user

        Args:
            message: WSMessage to broadcast
            user_id: If specified, only send to this user's connections
        """
        # Call event hooks
        await self._call_hooks(message.event_type, message.data)

        message_json = message.to_json()

        if user_id:
            # Send to specific user's connections
            if user_id in self.active_connections:
                disconnected = set()
                for websocket in self.active_connections[user_id]:
                    try:
                        await websocket.send_text(message_json)
                    except Exception as e:
                        logger.error(f"Error sending to user {user_id}: {e}")
                        disconnected.add(websocket)

                # Remove disconnected connections
                for ws in disconnected:
                    self.active_connections[user_id].discard(ws)
        else:
            # Broadcast to all connections
            disconnected = set()

            # Broadcast to all users
            for user_connections in self.active_connections.values():
                for websocket in user_connections:
                    try:
                        await websocket.send_text(message_json)
                    except Exception as e:
                        logger.error(f"Error broadcasting: {e}")
                        disconnected.add(websocket)

            # Broadcast to broadcast connections
            for websocket in self.broadcast_connections:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")
                    disconnected.add(websocket)

            # Clean up disconnected
            for ws in disconnected:
                self.broadcast_connections.discard(ws)

    async def broadcast_inventory_update(self, update_data: InventoryUpdateData):
        """Broadcast inventory update event"""
        # Determine event type based on stock status
        if update_data.is_out_of_stock:
            event_type = WSEventType.INVENTORY_OUT_OF_STOCK
        elif update_data.is_low_stock:
            event_type = WSEventType.INVENTORY_LOW_STOCK
        else:
            event_type = WSEventType.INVENTORY_UPDATED

        message = WSMessage(event_type, update_data.to_dict())
        await self.broadcast(message)

    async def broadcast_product_created(self, product_data: Dict[str, Any]):
        """Broadcast product created event"""
        message = WSMessage(WSEventType.PRODUCT_CREATED, product_data)
        await self.broadcast(message)

    async def broadcast_product_updated(self, product_data: Dict[str, Any]):
        """Broadcast product updated event"""
        message = WSMessage(WSEventType.PRODUCT_UPDATED, product_data)
        await self.broadcast(message)

    async def broadcast_sale_created(self, sale_data: Dict[str, Any]):
        """Broadcast sale created event"""
        message = WSMessage(WSEventType.SALE_CREATED, sale_data)
        await self.broadcast(message)

    async def broadcast_sale_completed(self, sale_data: Dict[str, Any]):
        """Broadcast sale completed event"""
        message = WSMessage(WSEventType.SALE_COMPLETED, sale_data)
        await self.broadcast(message)

    async def broadcast_sale_voided(self, sale_data: Dict[str, Any]):
        """Broadcast sale voided event"""
        message = WSMessage(WSEventType.SALE_VOIDED, sale_data)
        await self.broadcast(message)

    async def broadcast_notification(
        self, title: str, message: str, severity: str = "info"
    ):
        """
        Broadcast system notification

        Args:
            title: Notification title
            message: Notification message
            severity: 'info', 'warning', 'error', 'success'
        """
        data = {"title": title, "message": message, "severity": severity}
        msg = WSMessage(WSEventType.SYSTEM_NOTIFICATION, data)
        await self.broadcast(msg)

    def register_hook(
        self,
        event_type: WSEventType,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
    ):
        """
        Register a hook to be called when an event is broadcast

        Args:
            event_type: Event type to listen for
            handler: Async function that receives event data
        """
        if event_type not in self.event_hooks:
            self.event_hooks[event_type] = []
        self.event_hooks[event_type].append(handler)

    async def _call_hooks(self, event_type: WSEventType, data: Dict[str, Any]):
        """Call all registered hooks for an event type"""
        if event_type not in self.event_hooks:
            return

        for handler in self.event_hooks[event_type]:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Error calling hook for {event_type}: {e}")

    def get_connection_count(self, user_id: Optional[int] = None) -> int:
        """Get number of active connections"""
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        else:
            total = sum(len(conns) for conns in self.active_connections.values())
            total += len(self.broadcast_connections)
            return total

    def get_connected_users(self) -> list:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())


# Global connection manager instance
ws_manager = ConnectionManager()
