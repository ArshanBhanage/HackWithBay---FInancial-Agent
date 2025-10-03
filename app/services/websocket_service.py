"""WebSocket service for real-time updates."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store metadata for this connection
        self.connection_metadata[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info(f"WebSocket connected: {self.connection_metadata[websocket]['client_id']}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "client_id": self.connection_metadata[websocket]['client_id'],
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
            if websocket in self.connection_metadata:
                client_id = self.connection_metadata[websocket]['client_id']
                del self.connection_metadata[websocket]
                logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSocket clients."""
        if not self.active_connections:
            return
        
        # Create a copy of connections to avoid modification during iteration
        connections_to_remove = []
        
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                connections_to_remove.append(websocket)
        
        # Remove failed connections
        for websocket in connections_to_remove:
            self.disconnect(websocket)
    
    async def broadcast_violation(self, violation_data: Dict[str, Any]):
        """Broadcast a new violation to all connected clients."""
        message = {
            "type": "violation",
            "data": violation_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcast a new alert to all connected clients."""
        message = {
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_document_update(self, document_data: Dict[str, Any]):
        """Broadcast a document update to all connected clients."""
        message = {
            "type": "document_update",
            "data": document_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_stats_update(self, stats_data: Dict[str, Any]):
        """Broadcast dashboard stats update to all connected clients."""
        message = {
            "type": "stats_update",
            "data": stats_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections."""
        return [
            {
                "client_id": metadata["client_id"],
                "connected_at": metadata["connected_at"].isoformat(),
                "last_ping": metadata["last_ping"].isoformat()
            }
            for metadata in self.connection_metadata.values()
        ]
    
    async def ping_all(self):
        """Send ping to all connections to check if they're still alive."""
        connections_to_remove = []
        
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
                # Update last ping time
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_ping"] = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Error pinging connection: {e}")
                connections_to_remove.append(websocket)
        
        # Remove failed connections
        for websocket in connections_to_remove:
            self.disconnect(websocket)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

class WebSocketService:
    """Service for managing WebSocket connections and real-time updates."""
    
    def __init__(self):
        self.manager = websocket_manager
        self._running = False
        self._ping_task = None
    
    async def start(self):
        """Start the WebSocket service."""
        if self._running:
            return
        
        self._running = True
        # Start ping task to keep connections alive
        self._ping_task = asyncio.create_task(self._ping_loop())
        logger.info("WebSocket service started")
    
    async def stop(self):
        """Stop the WebSocket service."""
        self._running = False
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket service stopped")
    
    async def _ping_loop(self):
        """Background task to ping all connections periodically."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                if self._running:
                    await self.manager.ping_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
    
    async def handle_connection(self, websocket: WebSocket, client_id: str = None):
        """Handle a new WebSocket connection."""
        await self.manager.connect(websocket, client_id)
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    # Respond to ping
                    await self.manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                elif message.get("type") == "subscribe":
                    # Handle subscription requests
                    topics = message.get("topics", [])
                    logger.info(f"Client {self.manager.connection_metadata[websocket]['client_id']} subscribed to: {topics}")
                
                elif message.get("type") == "unsubscribe":
                    # Handle unsubscription requests
                    topics = message.get("topics", [])
                    logger.info(f"Client {self.manager.connection_metadata[websocket]['client_id']} unsubscribed from: {topics}")
                
        except WebSocketDisconnect:
            self.manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {e}")
            self.manager.disconnect(websocket)
    
    async def notify_violation_created(self, violation_data: Dict[str, Any]):
        """Notify all clients about a new violation."""
        await self.manager.broadcast_violation(violation_data)
    
    async def notify_alert_created(self, alert_data: Dict[str, Any]):
        """Notify all clients about a new alert."""
        await self.manager.broadcast_alert(alert_data)
    
    async def notify_document_processed(self, document_data: Dict[str, Any]):
        """Notify all clients about a processed document."""
        await self.manager.broadcast_document_update(document_data)
    
    async def notify_stats_updated(self, stats_data: Dict[str, Any]):
        """Notify all clients about updated dashboard stats."""
        await self.manager.broadcast_stats_update(stats_data)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {
            "active_connections": self.manager.get_connection_count(),
            "connections": self.manager.get_connection_info(),
            "service_running": self._running
        }

# Global WebSocket service instance
websocket_service = WebSocketService()
