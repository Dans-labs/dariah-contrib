"""Make a certain user root.

You cannot make a user root from within the system if no user is root.
This command directly accesses the database and makes a user root.

Which one is in `base.yaml` under the key `root`.

## Usage

`python3 root.py regime [test] [--only]`

Parameters
----------
regime: {development, production}
test: string `test`
    If passed, works with the test database (dariah_test)
only: string `--only`
    If passed, all existing users with `root` power are demoted to `office` power.
"""

import sys
from pymongo import MongoClient

from config import Config as C
from control.utils import serverprint, now, E

CB = C.base
ROOT = CB.root
DATABASE = CB.database


def makeUserRoot(database, eppn, only=False):
    """Gives a specific user the role of root.

    Parameters
    ----------
    database: string
        The name of the database in which the user lives
    eppn: string
        The `eppn` attribute of the user
    only: boolean, optional `False`
        If true, all other users with root role will be demoted to
        office power.
    """
    client = MongoClient()
    mongo = client[database]
    perms = {
        perm: mongo.permissionGroup.find({"rep": perm}, {"_id": True})[0]["_id"]
        for perm in {"root", "office"}
    }
    if only:
        mongo.user.update_many(
            {"group": perms["root"]},
            {"$set": {"group": perms["office"]}},
        )
    mongo.user.update_one(
        {"eppn": eppn}, {"$set": {"group": perms["root"]}},
    )
    mongo.collect.update_one(
        {"table": "user"}, {"$set": {"dateCollected": now()}}, upsert=True
    )


def main():
    regime = sys.argv[1] if len(sys.argv) > 1 else None
    test = sys.argv[2] == "test" if len(sys.argv) > 2 else False
    if not regime:
        serverprint("Don't know if this is development or production")
        return 1

    database = DATABASE["test"] if test else DATABASE.get(regime, None)
    if database is None:
        mode = f"""regime = {regime} {"test" if test else E}"""
        serverprint(
            f"""ERROR: No database configured for {mode}\n"""
            """See base.yaml"""
        )
        return 1
    eppn = ROOT[database]

    only = len(sys.argv) > 3 and sys.argv[3] == "--only"

    unique = "unique " if only else E
    serverprint(f"RESETTING {eppn} as {unique}root in {database}")
    makeUserRoot(database, eppn, only=only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
