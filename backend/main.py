from contextlib import asynccontextmanager
import asyncio
import signal
import sys
import time

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.websocket import WebSocketManager
from api.endpoints import router as api_router
from core.wifite_service import WifiteService
from utils.config import config
from utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()

    # Initialize managers
    websocket_manager = WebSocketManager()
    app.state.websocket_manager = websocket_manager

    # Initialize tool service
    wifite_service = WifiteService(websocket_manager)
    app.state.wifite_service = wifite_service

    # Start background tasks
    broadcast_task = asyncio.create_task(websocket_manager.broadcast_task())

    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    yield

    # Shutdown
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass

    await wifite_service.cleanup()
    await websocket_manager.disconnect_all()


app = FastAPI(
    title="Wifite2 Mobile Bridge",
    description="Real-time WebSocket bridge for wifite2 wireless auditing tool",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    return {"status": "running", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "connected_clients": len(app.state.websocket_manager.active_connections),
        "tool_status": app.state.wifite_service.status
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await app.state.websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})
            elif data.get("type") == "command":
                command = data.get("command")
                if command:
                    await app.state.wifite_service.handle_command(command, websocket)
    except WebSocketDisconnect:
        app.state.websocket_manager.disconnect(websocket)
    except Exception as e:
        app.state.websocket_manager.disconnect(websocket)
        # Log the error
        from utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    uvicorn.run("main:app", host=host, port=port, reload=False, log_level="info")