"""Change the sys path so that `test` modules can import `control` modules."""

import sys
import os

SERVER_PATH = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]

sys.path.insert(0, SERVER_PATH)
