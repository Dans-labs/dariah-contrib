import magic  # noqa
from control.utils import serverprint

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
    return Client(user, client)


class Client:
    """Wraps the Flask test client.

    Now we are able to do things for every request the client makes to the server.

    We use it for:

    *   writing an entry to a log file for each request;
    *   making sure that the client is logged in as the user for which it is
        created

    Another convenient use is, that test functions can inspect their
    `client` argument and can see to which user (`eppn`) it belongs.
    """

    urllog = open(URL_LOG, 'w')
    """We open the log file one the class is defined.

    The log file handle is a class attribute, not an instance attribute.
    """

    def __init__(self, user, cl):
        """Wrap the user in a client.

        Parameters
        ----------
        user: string
            The `eppn` of the user for which the client has been made.
            See `makeClient`.
        cl: fixture
            A Flask object actiing as a client that fires requests at the server.
        """
        self.cl = cl
        self.user = user

    def get(self, *args, **kwargs):
        """Wrapper for `client.get()`. """

        self.identify()
        cl = self.cl

        Client.urllog.write(f"{self.user}\t{args[0]}\n")
        return cl.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """Wrapper for `client.post()`. """

        self.identify()
        cl = self.cl

        Client.urllog.write(f"{self.user}\t{args[0]}\n")
        return cl.post(*args, **kwargs)

    def identify(self):
        user = self.user
        cl = self.cl

        url = "/logout" if user == "public" else f"/login?eppn={user}"
        cl.get(url)
        response = cl.get("/whoami")
        actualUser = response.get_data(as_text=True)
        good = user == actualUser
        if not good:
            serverprint(f"USER={actualUser} (=/={user})")
        assert good
