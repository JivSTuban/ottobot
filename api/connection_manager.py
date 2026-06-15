"""
api/connection_manager.py — WebSocket ConnectionManager per FastAPI pattern.

Tracks active WebSocket connections and provides connect/disconnect lifecycle.
Disconnect is idempotent — safe to call even if the socket was never connected
or was already removed.
"""

from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept the WebSocket handshake and register the connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket from the active list. Idempotent."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
