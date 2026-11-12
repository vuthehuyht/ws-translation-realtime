"""AppSync Integration: AWS AppSync Events WebSocket Realtime Fan-out.

Wraps publishSubtitleEvent mutations to fan out subtitle tokens and final sentences
to up to 1,000 concurrent listeners per room with offline mock support.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AppSyncClient:
    """Interface for AppSync GraphQL / Events publisher."""

    async def publish_subtitle_event(
        self,
        room_id: str,
        target_lang: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> bool:
        raise NotImplementedError


class MockAppSyncClient(AppSyncClient):
    """In-memory offline mock for local development and pytest suites."""

    def __init__(self) -> None:
        self.published_events: list[dict[str, Any]] = []

    async def publish_subtitle_event(
        self,
        room_id: str,
        target_lang: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> bool:
        event = {
            "roomId": room_id,
            "targetLang": target_lang,
            "eventType": event_type,
            "payload": payload,
        }
        self.published_events.append(event)
        logger.info(
            "Mock AppSync published event: room=%s lang=%s type=%s",
            room_id,
            target_lang,
            event_type,
        )
        return True


_appsync_instance: AppSyncClient | None = None


def get_appsync_client() -> AppSyncClient:
    """Retrieve singleton AppSyncClient instance."""
    global _appsync_instance
    if _appsync_instance is None:
        _appsync_instance = MockAppSyncClient()
    return _appsync_instance


def set_appsync_client(client: AppSyncClient) -> None:
    """Explicitly override AppSync client for test dependency injection."""
    global _appsync_instance
    _appsync_instance = client
