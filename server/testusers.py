"""Inserts test users in the development database.

This is used after restoring the contents of the production database
as the development database on the development machine.
In order to log in, we need users with a local authority.


We add the same users as we have for testing situations.
"""

import sys

# from datetime import datetime as dt
from pymongo import MongoClient

from config import Config as C, Names as N
from control.utils import pick as G


CB = C.base
CC = C.clean

DATABASE = CB.database[N.development]

USER = CC.user


def main():
    client = MongoClient()
    sys.stdout.write(f"ADD TEST USERS to DATABASE {DATABASE} ... ")
    db = client[DATABASE]

    idFromIso = {G(record, N.iso): G(record, N._id) for record in db.country.find()}
    idFromGroup = {
        G(record, N.rep): G(record, N._id) for record in db.permissionGroup.find()
    }

    users = []
    for user in USER:
        u = dict(x for x in user.items())
        u[N.group] = idFromGroup[u[N.group]]
        if N.country in u:
            u[N.country] = idFromIso[u[N.country]]
        users.append(u)

    db.user.insert_many(users)

    sys.stdout.write("DONE\n")


if __name__ == "__main__":
    main()
