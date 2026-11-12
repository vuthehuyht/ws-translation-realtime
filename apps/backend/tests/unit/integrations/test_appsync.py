"""Unit tests for AWS AppSync Events Subtitle Fan-out Integration (app.integrations.appsync)."""

from app.integrations.appsync import get_appsync_client


async def test_appsync_subtitle_event_fanout() -> None:
    appsync = get_appsync_client()
    room_id = "test-fanout-room-99"

    payload = {
        "sequence": 1,
        "isFinal": True,
        "translatedText": "Xin chào thế giới",
        "audioUrl": "https://cdn.example.com/tts/test.mp3",
    }

    success = await appsync.publish_subtitle_event(
        room_id=room_id,
        target_lang="vi",
        event_type="SUBTITLE_FINAL",
        payload=payload,
    )
    assert success is True
