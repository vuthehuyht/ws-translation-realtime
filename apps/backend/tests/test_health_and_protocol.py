import pytest
from httpx import AsyncClient

from app.schemas.ws_protocol import BinaryAudioFrame


async def test_health_endpoint_returns_ok(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ws-translation-backend"


def test_binary_audio_frame_roundtrip_big_endian() -> None:
    pcm_payload = b"\x01\x02\x03\x04" * 800
    frame = BinaryAudioFrame(
        seq_id=42,
        timestamp_ms=1731196800000,
        codec=1,
        flags=0b01,
        audio_payload=pcm_payload,
    )

    packed = frame.to_bytes()
    assert len(packed) == 16 + len(pcm_payload)

    unpacked = BinaryAudioFrame.from_bytes(packed)
    assert unpacked.seq_id == 42
    assert unpacked.timestamp_ms == 1731196800000
    assert unpacked.codec == 1
    assert unpacked.is_speech is True
    assert unpacked.end_of_turn is False
    assert unpacked.audio_payload == pcm_payload


def test_binary_audio_frame_rejects_short_header() -> None:
    with pytest.raises(ValueError, match="16 bytes"):
        BinaryAudioFrame.from_bytes(b"\x00" * 15)
