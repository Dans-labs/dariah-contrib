import sys

from control.db import Db
from control.workflow.compute import Workflow
from control.utils import serverprint, E


def computeWorkflow(regime, test):
    if not regime:
        serverprint("Don't know if this is development or production")
        return 1

    mode = f"""regime = {regime} {"test" if test else E}"""
    serverprint(f"WORKFLOW RESET for {mode}")
    DB = Db(regime, test)
    WF = Workflow(DB)
    WF.initWorkflow(drop=True)
    return 0


regime = sys.argv[1] if len(sys.argv) > 1 else None
test = sys.argv[2] == "test" if len(sys.argv) > 2 else False
sys.exit(computeWorkflow(regime, test))
