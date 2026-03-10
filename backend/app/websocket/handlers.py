import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from app.utils.security import decode_token
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/board/{project_id}")
async def board_websocket(
    websocket: WebSocket,
    project_id: str,
    token: str = Query(...),
) -> None:
    """WebSocket endpoint for real-time board updates.

    Clients connect with a JWT token as a query parameter for authentication.
    Once connected, they receive broadcast messages for board changes in the project.
    """
    # Verify JWT token from query param
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await manager.connect(project_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed in the future
            logger.debug("Received WS message from user %s in project %s: %s", user_id, project_id, data)
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
