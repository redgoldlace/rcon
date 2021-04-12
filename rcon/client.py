import asyncio
import functools

from typing import Optional, Tuple

from .errors import AuthenticationFailed, ConnectionFailed
from .message import Message
from .protocol import RCONProtocol


AUTH = 3
AUTH_RESPONSE = 2
EXECUTE_COMMAND = 2
RESPONSE_VALUE = 0
# Note that the repetition in the above is not an error:
# SERVERDATA_AUTH_RESPONSE and SERVERDATA_EXECCOMMAND both have a numeric value of 2.
# There's been some transliteration of names here for clarity, but hopefully you get the gist.


def ensure_connection(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.connected:
            raise RuntimeError("Connection is closed.")

        return func(self, *args, **kwargs)

    return wrapper

class Client:
    def __init__(self, host: str, port: int, password: str, *, timeout: float = 10) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.connected = False
        self._packet_id = 2  # We start this at 2 because we use 1 while connecting.

    async def connect(self):
        """Tries to connect to the remote server and authorise an RCON connection."""
        loop = asyncio.get_event_loop()
        # Below is an incredibly dumb typing quirk.
        # Essentially what we have to do is try and "override" the (BaseTransport, BaseProtocol) type that is inferred
        # from the stubs because it's incorrect for our use case. I don't want to imagine how bad this would be if I
        # was bothering to type things properly. Bleh.
        try:
            pair: Tuple[asyncio.Transport, RCONProtocol] = await loop.create_connection(
                lambda: RCONProtocol(self), self.host, self.port
            )  # type: ignore
        except OSError:
            message = (
                f"Could not connect to the server at host {self.host} with port {self.port}."
                "The host/port may be incorrect, or you may be banned/blacklisted."
            )

            raise ConnectionFailed(message)

        self._transport, self._protocol = pair

        # Now that we have a connection open, the first thing we need to do is send an auth packet.
        auth_message = Message(packet_id=1, message_type=AUTH, body=self.password)
        self._transport.write(auth_message.to_bytes())
        # This will be an empty packet. We can ignore it.
        await self._protocol.wait_for_message(1)
        # We have two possibilities here:
        #   - If authentication was a success, the ID of the next packet will be the one we set earlier (so just 1)
        #   - Otherwise, the ID of the next packet will be -1 to represent failure.
        done, pending = await asyncio.wait(
            [self._protocol.wait_for_message(1), self._protocol.wait_for_message(-1)],
            return_when=asyncio.FIRST_COMPLETED
        )

        # We don't want these to continue.
        for future in pending:
            future.cancel()

        if not done:
            raise AuthenticationFailed("The server did not send an authentication response.")

        result: Message = done.pop().result()
        if result.packet_id == -1:
            raise AuthenticationFailed("Authentication failed! Was the password incorrect?")
 
        self.connected = True

    @ensure_connection
    async def send(self, body: str) -> str:
        """Sends a message to the remote server and returns the response as a string.
        This method will raise `RuntimeError` if it is called while the client is disconnected.
        """
        # Some packets may be in multiple pieces if the response is especially long. It's difficult to tell when
        # a packet has been split, but since responses are guaranteed to arrive in order, we can abuse that with a
        # dummy packet to make sure we've got all of the pieces before returning a result.
        message = Message(packet_id=self._packet_id, message_type=EXECUTE_COMMAND, body=body)
        dummy = Message(packet_id=self._packet_id, message_type=RESPONSE_VALUE, body="")

        self._transport.write(message.to_bytes())
        self._transport.write(dummy.to_bytes())

        # This is an incredibly lazy approach to packet IDs. It's theoretically prone to overflows, but I don't care.
        # If you're sending that many packets, you don't deserve this library. Go away.
        self._packet_id += 1
        results = []

        while True:
            received = await self._protocol.wait_for_message(message.packet_id)
            if not received.body:
                break

            results.append(message.body)

        return "".join(results)

    @ensure_connection
    async def close(self):
        """Close the connection to the remote server."""
        self._transport.close()
        self.connected = False
