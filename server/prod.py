import os
import sys

from control.utils import E, SLASH, DOT


dir = os.path.dirname(__file__)
targetDir = f"""{dir}{SLASH if dir else E}"""
os.chdir(targetDir)
sys.path.append(DOT)

from index import factory  # noqa

application = factory('production')
