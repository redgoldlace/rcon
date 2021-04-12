import asyncio
import typing

from collections import defaultdict

from .message import Message


if typing.TYPE_CHECKING:
    from .client import Client


class RCONProtocol(asyncio.Protocol):
    def __init__(self, client: "Client") -> None:
        self._messages = defaultdict(asyncio.Queue)
        self._client = client
        self._transport = None

    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        self._transport = transport

    def data_received(self, data: bytes) -> None:
        message = Message.from_bytes(data)
        self._messages[message.packet_id].put_nowait(message)

    async def wait_for_message(self, packet_id: int) -> Message:
        result = await asyncio.wait_for(self._messages[packet_id].get(), timeout=self._client.timeout)
        if self._messages[packet_id].empty():
            del self._messages[packet_id]

        return result