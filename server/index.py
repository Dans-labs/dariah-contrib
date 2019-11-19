import sys
from control.app import appFactory
from control.utils import serverprint


DEBUG = False
TEST = False


def factory(regime, **kwargs):
    if regime not in {"production", "development"}:
        serverprint(f"REGIME: illegal value: {regime}")
        sys.exit()
    serverprint(f"REGIME: {regime}")
    return appFactory(regime, DEBUG, TEST, **kwargs)


if __name__ == "__main__":
    app = factory(None)
