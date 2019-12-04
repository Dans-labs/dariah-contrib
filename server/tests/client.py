URL_LOG = """tests/urllog.txt"""
"""The name of the url log file.

This is a single file in which each request that a client
fires at the server is logged.
After testing is will be analysed by `analysis`.
"""


def makeClient(app, user):
    """Logs in a specific user.

    Parameters
    ----------
    app: object
    user: string
        Identity of the user (eppn)
    """

    client = app.test_client()

    good = True
    if user != "public":
        response = client.get(f"/login?eppn={user}")
        if response.status_code != 302:
            good = False
    if good:
        return Client(user, client)
    return None


class Client:
    """Wraps the Flask test client.

    Now we are able to do things for every request the client makes to the server.

    For the moment, we use it to log each request to file.

    Another convenient use is, that test functions can inspect their
    `client` argument and can see to which user (`eppn`) it belongs.
    """

    urllog = open(URL_LOG, 'w')
    """We open the log file one the class is defined.

    The log file handle is a class attribute, not an instance attribute.
    """

    def __init__(self, user, client):
        """Wrap the user in a client.

        Parameters
        ----------
        user: string
            The `eppn` of the user for which the client has been made.
            See `makeClient`.
        client: fixture
            A Flask object actiing as a client that fires requests at the server.
        """
        self.cl = client
        self.user = user

    def get(self, *args, **kwargs):
        """Wrapper for `client.get()`. """

        Client.urllog.write(f"{self.user}\t{args[0]}\n")
        return self.cl.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """Wrapper for `client.post()`. """

        Client.urllog.write(f"{self.user}\t{args[0]}\n")
        return self.cl.post(*args, **kwargs)
