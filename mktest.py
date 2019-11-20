import sys
import os


PATH = os.path.split(os.path.realpath(__file__))[0]

TESTS = f"{PATH}/server/tests"

INDEX = f"{os.path.realpath(sys.argv[1])}/index.md"

with os.scandir(TESTS) as it:
    entries = sorted(
        os.path.splitext(entry.name)[0] for entry in it
        if (
            not entry.name.startswith(".")
            and entry.is_file()
            and entry.name.endswith(".py")
        )
    )

with open(INDEX, 'w') as fh:
    fh.write("\n\n".join(f"[{entry}]({entry}.html)" for entry in entries))
