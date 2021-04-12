def _encode_int(value: int) -> bytes:
    return value.to_bytes(length=4, byteorder="little")


def _decode_int(data: bytes) -> int:
    return int.from_bytes(data, byteorder="little", signed=True)


class Message:
    def __init__(self, *, packet_id: int, message_type: int, body: str) -> None:
        self.message_type = message_type
        self.packet_id = packet_id
        self.body = body
        self.raw_body = self.body.encode("ascii")
        self.packet_size = len(self.raw_body) + 14

    def to_bytes(self) -> bytearray:
        buffer = bytearray(self.packet_size)

        # The first field is the packet size. From https://developer.valvesoftware.com/wiki/Source_RCON_Protocol:
        #   the packet size field itself is not included when determining the size of the packet,
        #   so the value of this field is always 4 less than the packet's actual length.
        buffer[0:4] = _encode_int(self.packet_size - 4)
        buffer[4:8] = _encode_int(self.packet_id)
        buffer[8:12] = _encode_int(self.message_type) # type: ignore
        buffer[12:self.packet_size - 2] = self.raw_body
        # You may notice that we have two remaining bytes that will just be null bytes.
        # The first is the terminator for the body, and the second is the terminator for the packet as a whole.

        return buffer

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        if not 14 <= len(data) <= 4100:
            raise ValueError("Packet size must be between 14 and 4100 bytes.")

        new = cls(
            packet_id=_decode_int(data[4:8]),
            message_type=_decode_int(data[8:12]),
            body=data[12:-2].decode("ascii")
        )

        return new