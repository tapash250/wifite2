from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import time
import logging

from core.wifite_service import WifiteService, ToolStatus
from utils.config import config

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models
class ToolControlRequest(BaseModel):
    interface: Optional[str] = None
    # Add other tool-specific parameters as needed
    # For wifite2, we could add things like:
    # power: Optional[int] = None
    # dictionary: Optional[str] = None
    # infinite: bool = False
    # etc.


class ToolStatusResponse(BaseModel):
    status: str
    pid: Optional[int] = None
    output_lines: int = 0
    running_time: float = 0.0
    command: str = ""


@router.get("/health")
async def health_check(request):
    """Health check endpoint"""
    tool_service: WifiteService = request.app.state.wifite_service
    websocket_manager = request.app.state.websocket_manager
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "connected_clients": len(websocket_manager.active_connections),
        "tool_status": tool_service.status.value,
        "version": "0.1.0"
    }


@router.post("/tool/start")
async def start_tool(request: ToolControlRequest, background_tasks: BackgroundTasks, request_obj):
    """Start the wifite2 tool"""
    try:
        tool_service: WifiteService = request_obj.app.state.wifite_service
        
        # If interface is provided in request, we could update the service
        # For now, we'll just start with default configuration
        await tool_service.start_tool()
        
        return {
            "status": "started",
            "message": "Wifite2 tool started successfully",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to start tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start tool: {str(e)}")


@router.post("/tool/stop")
async def stop_tool(request_obj):
    """Stop the wifite2 tool"""
    try:
        tool_service: WifiteService = request_obj.app.state.wifite_service
        await tool_service.stop_tool()
        
        return {
            "status": "stopped",
            "message": "Wifite2 tool stopped successfully",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to stop tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop tool: {str(e)}")


@router.get("/tool/status", response_model=ToolStatusResponse)
async def get_tool_status(request_obj):
    """Get current status of the wifite2 tool"""
    try:
        tool_service: WifiteService = request_obj.app.state.wifite_service
        
        if tool_service.process_info:
            running_time = time.time() - tool_service.process_info.start_time
            return ToolStatusResponse(
                status=tool_service.status.value,
                pid=tool_service.process_info.pid,
                output_lines=tool_service.process_info.output_lines,
                running_time=running_time,
                command=tool_service.process_info.command
            )
        else:
            return ToolStatusResponse(
                status=tool_service.status.value,
                pid=None,
                output_lines=0,
                running_time=0.0,
                command=""
            )
    except Exception as e:
        logger.error(f"Failed to get tool status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tool status: {str(e)}")


@router.get("/config")
async def get_config():
    """Return safe configuration values for the frontend"""
    # Return only non-sensitive configuration
    return {
        "tool_interface": config.tool_interface,
        "tool_timeout": config.tool_timeout,
        "ws_heartbeat_interval": config.ws_heartbeat_interval,
        "powersync_enabled": config.powersync_enabled,
        "powersync_interval": config.powersync_interval,
        "version": "0.1.0"
    }


# Optional: Add a WebSocket info endpoint for debugging
@router.get("/ws/info")
async def websocket_info(request_obj):
    """Get WebSocket connection info"""
    websocket_manager = request_obj.app.state.websocket_manager
    return {
        "active_connections": len(websocket_manager.active_connections),
        "connections": [
            {"id": websocket_manager.connection_id_map.get(ws, "unknown")}
            for ws in websocket_manager.active_connections
        ]
    }