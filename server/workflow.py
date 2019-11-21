import sys
from pymongo import MongoClient

from control.db import Db
from control.workflow.compute import Workflow


def computeWorkflow(test):
    MONGO = MongoClient()
    myDb = MONGO.dariah_clean if test else MONGO.dariah
    DB = Db(myDb)
    WF = Workflow(DB)
    WF.initWorkflow(drop=True)


test = sys.argv[1] if len(sys.argv) > 1 else None
computeWorkflow(test)
