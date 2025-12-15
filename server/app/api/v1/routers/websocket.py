"""
Vendly POS - WebSocket Router
==============================
Real-time communication endpoints for inventory, sales, and notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
import logging
from typing import Optional

from app.core.websocket import ws_manager, WSEventType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/inventory")
async def websocket_inventory(websocket: WebSocket, user_id: Optional[int] = Query(None)):
    """
    WebSocket endpoint for real-time inventory updates
    
    Query Parameters:
        - user_id: Optional user ID for user-specific updates
    
    Events received:
        - inventory_updated: Product quantity changed
        - inventory_low_stock: Product below minimum quantity
        - inventory_out_of_stock: Product quantity is zero
    """
    await ws_manager.connect(websocket, user_id)
    
    try:
        # Keep connection alive
        while True:
            # Just receive any messages and ignore them
            # Real updates come from server broadcasts
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected from inventory WebSocket")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(websocket, user_id)


@router.websocket("/sales")
async def websocket_sales(websocket: WebSocket, user_id: Optional[int] = Query(None)):
    """
    WebSocket endpoint for real-time sales updates
    
    Query Parameters:
        - user_id: Optional user ID for user-specific updates
    
    Events received:
        - sale_created: New sale initiated
        - sale_completed: Sale completed
        - sale_voided: Sale voided/cancelled
    """
    await ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected from sales WebSocket")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(websocket, user_id)


@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket, user_id: Optional[int] = Query(None)):
    """
    WebSocket endpoint for system notifications
    
    Query Parameters:
        - user_id: Optional user ID for user-specific notifications
    
    Events received:
        - system_notification: System alerts and messages
        - inventory_low_stock: Low stock alerts
        - inventory_out_of_stock: Out of stock alerts
    """
    await ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected from notifications WebSocket")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(websocket, user_id)


@router.websocket("/all")
async def websocket_all(websocket: WebSocket, user_id: Optional[int] = Query(None)):
    """
    WebSocket endpoint for all real-time events
    Consolidates inventory, sales, and notification events
    
    Query Parameters:
        - user_id: Optional user ID for user-specific updates
    
    Events received:
        - All event types from other endpoints
    """
    await ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected from all events WebSocket")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(websocket, user_id)


# Health check endpoint for WebSocket status
@router.get("/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "total_connections": ws_manager.get_connection_count(),
        "connected_users": len(ws_manager.get_connected_users()),
        "active_user_ids": ws_manager.get_connected_users()
    }
