# backend/app/websocket/manager.py
# WebSocket 연결 관리자 - 프로젝트별 실시간 보드 업데이트
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


def _client_info(websocket: WebSocket) -> str:
    """WebSocket 클라이언트 정보를 안전하게 추출한다."""
    client = websocket.client
    if client is None:
        return "unknown"
    return f"{client.host}:{client.port}"


class ConnectionManager:
    """프로젝트별 WebSocket 연결을 관리하여 실시간 보드 업데이트를 지원한다."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        """WebSocket 연결을 수락하고 프로젝트 풀에 추가한다."""
        await websocket.accept()
        self.active_connections[project_id].append(websocket)
        logger.info("WebSocket 연결: project=%s, client=%s", project_id, _client_info(websocket))

    def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        """프로젝트 풀에서 WebSocket 연결을 제거한다."""
        self.active_connections[project_id].remove(websocket)
        if not self.active_connections[project_id]:
            del self.active_connections[project_id]
        logger.info("WebSocket 해제: project=%s, client=%s", project_id, _client_info(websocket))

    async def broadcast(
        self,
        project_id: str,
        message: dict[str, Any],
        exclude: WebSocket | None = None,
    ) -> None:
        """프로젝트의 모든 연결에 JSON 메시지를 브로드캐스트한다."""
        connections = self.active_connections.get(project_id, [])
        for connection in connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception:
                    logger.warning(
                        "메시지 전송 실패: client=%s, project=%s",
                        _client_info(connection),
                        project_id,
                    )


manager = ConnectionManager()
