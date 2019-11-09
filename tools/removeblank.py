import sys
from pymongo import MongoClient

MONGO = None
DOCTYPE = "contrib"


def dbaccess():
    global MONGO
    clientm = MongoClient()
    MONGO = clientm.dariah


def serverprint(msg):
    sys.stdout.write(f"""{msg}\n""")
    sys.stdout.flush()


def getBlanks():
    """Retrieve blank documents

  Blank documents have been inserted in the database without editing them.
  When they pile up, it might be handy to remove them.
  """

    blankFilter = {
        "title": "no title",
    }
    documents = list(MONGO[DOCTYPE].find(blankFilter))

    serverprint(f"{len(documents)} blank documents")

    checkedDocuments = []
    for document in documents:
        checkedDocument = {
            "modifiedBy": "UNKNOWN",
        }
        for (field, data) in document.items():
            if field == "_id":
                checkedDocument["_id"] = data
            elif field in {"title", "creator", "dateCreated"}:
                continue
            elif field == "modified":
                if data:
                    checkedDocument["modifiedBy"] = data[0].split()[0].split("@")[0]
            else:
                if data:
                    checkedDocument.setdefault("nonempty", {})[field] = str(data)
        checkedDocuments.append(checkedDocument)

    sortedDocuments = sorted(checkedDocuments, key=lambda d: d["modifiedBy"])

    blankDocuments = []

    for (i, document) in enumerate(sortedDocuments):
        serverprint(f"""Blank doc {i + 1} = {document['_id']} by {document["modifiedBy"]}""")
        if "nonempty" in document:
            serverprint(f"""\tnon empty: {str(document["nonempty"])}""")
        else:
            blankDocuments.append(document["_id"])
    serverprint(f"{len(blankDocuments)} truly blank documents")

    return blankDocuments


def delDocs(docIds):
    serverprint(f"{len(docIds)} documents to remove")
    i = 0
    for docId in docIds:
        sys.stderr.write(f"Deleting {docId} ...")
        MONGO[DOCTYPE].delete_one({"_id": docId})
        sys.stderr.write("done\n")
        i += 1
    serverprint(f"{i} documents removed")


dbaccess()
docIds = getBlanks()
delDocs(docIds)
