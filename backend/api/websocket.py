import asyncio
import time
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_id_map: Dict[WebSocket, str] = {}
        self._broadcast_queue: asyncio.Queue = asyncio.Queue()
        self._broadcast_task: asyncio.Task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Assign a simple ID based on count and timestamp
        conn_id = f"{len(self.active_connections)}-{int(time.time())}"
        self.connection_id_map[websocket] = conn_id
        logger.info(f"WebSocket connected: {conn_id}. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            conn_id = self.connection_id_map.get(websocket, "unknown")
            self.active_connections.remove(websocket)
            if websocket in self.connection_id_map:
                del self.connection_id_map[websocket]
            logger.info(f"WebSocket disconnected: {conn_id}. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        # Put the message in the queue to be processed by the broadcast task
        await self._broadcast_queue.put(message)

    async def broadcast_task(self):
        """Background task to process the broadcast queue and send to all connections."""
        while True:
            message = await self._broadcast_queue.get()
            if message is None:  # Allow for graceful shutdown
                break
            # We create a list of tasks to send to all connections, but we don't wait for all to complete
            # because we want to continue processing the queue.
            # However, we must handle exceptions per connection to avoid breaking the loop.
            tasks = []
            for connection in self.active_connections:
                task = asyncio.create_task(self._safe_send(connection, message))
                tasks.append(task)
            # Wait for all sends to complete (or at least not leave pending tasks)
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_send(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            self.disconnect(websocket)

    # Event-specific senders (customize as needed for wifite2)
    async def send_scan_update(self, data: dict):
        await self.broadcast({
            "type": "scan_update",
            "data": data,
            "timestamp": time.time()
        })

    async def send_scan_target(self, data: dict):
        await self.broadcast({
            "type": "scan_target",
            "data": data,
            "timestamp": time.time()
        })

    async def send_attack_start(self, data: dict):
        await self.broadcast({
            "type": "attack_start",
            "data": data,
            "timestamp": time.time()
        })

    async def send_attack_progress(self, data: dict):
        await self.broadcast({
            "type": "attack_progress",
            "data": data,
            "timestamp": time.time()
        })

    async def send_attack_complete(self, data: dict):
        await self.broadcast({
            "type": "attack_complete",
            "data": data,
            "timestamp": time.time()
        })

    async def send_process_output(self, pid: int, command: str, line: str, stream: str = "stdout"):
        await self.broadcast({
            "type": "process_output",
            "pid": pid,
            "command": command,
            "line": line,
            "stream": stream,
            "timestamp": time.time()
        })

    async def send_error(self, error_type: str, message: str, details: dict = None):
        await self.broadcast({
            "type": "error",
            "error_type": error_type,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        })

    async def send_system_event(self, event: str, data: dict = None):
        await self.broadcast({
            "type": "system_event",
            "event": event,
            "data": data or {},
            "timestamp": time.time()
        })

    async def start(self):
        """Start the broadcast task."""
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self.broadcast_task())

    async def stop(self):
        """Stop the broadcast task and clean up."""
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        # Disconnect all active connections
        for websocket in list(self.active_connections):
            self.disconnect(websocket)