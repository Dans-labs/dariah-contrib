from pymongo import MongoClient

from control.db import Db
from control.workflow.compute import Workflow


def computeWorkflow(test):
    MONGO = MongoClient()
    myDb = MONGO.dariah
    DB = Db(myDb)
    WF = Workflow(DB)
    WF.initWorkflow(drop=True)


computeWorkflow()
