class ConnectionFailed(Exception):
    """An exception raised if connecting fails. This is usually because the remote host or port were incorrect,
    but the connection can be refused if the user is banned/blacklisted.
    """

class AuthenticationFailed(Exception):
    """An exception raised if authentication fails. This is usually caused by an incorrect password."""