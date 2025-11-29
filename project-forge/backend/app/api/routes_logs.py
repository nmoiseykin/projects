"""Logs API routes."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from app.core.config import settings
from app.core.logging import logger
import asyncio
from pathlib import Path

router = APIRouter(prefix="/logs", tags=["logs"])

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for live log streaming."""
    await manager.connect(websocket)
    
    log_file = Path(settings.APP_LOG_FILE)
    if not log_file.exists():
        await websocket.send_text("Log file not found.")
        manager.disconnect(websocket)
        return
    
    try:
        # Send last 100 lines
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-100:]:
                await websocket.send_text(line.strip())
        
        # Tail the file
        with open(log_file, "r") as f:
            # Go to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    await websocket.send_text(line.strip())
                else:
                    await asyncio.sleep(0.1)
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/tail")
async def tail_logs(lines: int = 100):
    """Get last N lines of log file (SSE)."""
    log_file = Path(settings.APP_LOG_FILE)
    
    if not log_file.exists():
        return StreamingResponse(
            iter(["Log file not found.\n"]),
            media_type="text/plain"
        )
    
    def generate():
        with open(log_file, "r") as f:
            file_lines = f.readlines()
            for line in file_lines[-lines:]:
                yield line
    
    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


