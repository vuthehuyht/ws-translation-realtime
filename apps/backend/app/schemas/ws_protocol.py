import struct
from dataclasses import dataclass

# Big-endian 16-byte header (>IQBBH):
# seq_id (uint32: 4B), timestamp_ms (uint64: 8B), codec (uint8: 1B),
# flags (uint8: 1B), reserved (uint16: 2B)
HEADER_FORMAT = ">IQBBH"
HEADER_SIZE_BYTES = 16


@dataclass(frozen=True, slots=True)
class BinaryAudioFrame:
    seq_id: int
    timestamp_ms: int
    codec: int
    flags: int
    audio_payload: bytes
    reserved: int = 0

    @property
    def is_speech(self) -> bool:
        return bool(self.flags & 0b01)

    @property
    def end_of_turn(self) -> bool:
        return bool(self.flags & 0b10)

    def to_bytes(self) -> bytes:
        header = struct.pack(
            HEADER_FORMAT,
            self.seq_id,
            self.timestamp_ms,
            self.codec,
            self.flags,
            self.reserved,
        )
        return header + self.audio_payload

    @classmethod
    def from_bytes(cls, raw: bytes) -> "BinaryAudioFrame":
        if len(raw) < HEADER_SIZE_BYTES:
            raise ValueError(
                f"Binary audio frame must be at least {HEADER_SIZE_BYTES} bytes, got {len(raw)}"
            )
        seq_id, timestamp_ms, codec, flags, reserved = struct.unpack(
            HEADER_FORMAT, raw[:HEADER_SIZE_BYTES]
        )
        return cls(
            seq_id=seq_id,
            timestamp_ms=timestamp_ms,
            codec=codec,
            flags=flags,
            reserved=reserved,
            audio_payload=raw[HEADER_SIZE_BYTES:],
        )
