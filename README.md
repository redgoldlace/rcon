# RCON
An asynchronous library for the RCON protocol.

## Note
I originally wrote this for a friend who wanted to use Pavlov VR's RCON interface. Unfortunately what Pavlov VR calls
RCON is not actually the RCON protocol that I implemented. I, of course, found this out only after I had already written
all of this. No, I am not happy.

Anyway I haven't actually been able to test any of this. Lemme know if it works. Thanks.

## Getting started
Install via pypi:

```sh
python -m pip install -U git+https://github.com/kaylynn234/rcon
```
The above can differ depending on your environment. On windows, try `py` instead of `python`.
On some systems, you might want `python3` instead of `python`.

I've only tested this on Python 3.9 but in theory it should work on anything Python 3.8 and up.
If you're lucky it might even work on Python 3.7, but no promises.

Usage is pretty simple. Import `rcon`, and then construct a `Client` instance:
```py
client = rcon.Client("127.0.0.1", 1234, "your_password")
```
Obviously make sure to replace these placeholders with real credentials.
The first argument is the address of the remote server, followed by the port it's running on, and then the RCON
password.

You can also use the timeout kwarg to control how long to wait for a response from the server before
raising an error:
```py
client = rcon.Client("127.0.0.1", 1234, "your_password", timeout=...)
```
The default timeout is 10 seconds.

Once you have a client instance, you need to connect to the remote server before you can do anything useful:
```py
await client.connect()
```

Then you can send commands as you'd expect:
```py
response = await client.send("...")
```
`response` will be the remote server's response to the supplied command. It is always of type `str` - there's no
guarantees on what kind of data the server will return, so the library will just give you the response
as a string. If you need to deserialize JSON or similar, that's on you.

Once you're done, make sure to close the client:
```py
await client.close()
```

## Documentation?
No. This doesn't warrant documentation. I don't need to explain anything here in any more detail than this.