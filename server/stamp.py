import sys
import os
import re
from shutil import copyfile
from glob import glob

from control.utils import serverprint

STAMP_DIRS = ["static/css", "static/js"]
CALL_FILES = ["server/control/templates/index.html"]

callRe = re.compile(
    r"""
    [ ]
    (src|href)
    =
    ['"]
    ([^'"]*?)
    ((?:\.[a-zA-Z0-9]+)?)
    ['"]
""",
    re.X,
)


def changedCallFiles(origFile):
    if not os.path.exists(origFile):
        serverprint(f"WARNING: caller file {origFile} not found. Skipping.")
        return
    changes = set()
    removes = set()
    with open(origFile) as of:
        text = of.read()
        calls = callRe.findall(text)
        for (att, base, ext) in calls:
            calledPath = f"{base[1:]}{ext}"

            if all(not calledPath.startswith(stampDir) for stampDir in STAMP_DIRS):
                continue
            if not os.path.exists(calledPath):
                serverprint(f"WARNING: called file {calledPath} not found. Skipping.")
                continue
            calledGlob = f"{base[1:]}-[0-9][0-9]*{ext}"
            slug = int(round(os.path.getmtime(calledPath)))
            (calledDir, calledFile) = os.path.split(calledPath)
            calledSlugPath = f"{base[1:]}-{slug}{ext}"
            for slugPath in glob(calledGlob):
                if slugPath != calledSlugPath:
                    removes.add(slugPath)
            changes.add((calledPath, calledSlugPath))
    return (text, changes, removes)


def main():
    args = sys.argv[1:]
    unstamp = args and args[0] == "un"
    texts = {}
    mapFile = {}
    changes = {}
    changed = set()
    removes = set()
    for callFile in CALL_FILES:
        (base, ext) = os.path.splitext(callFile)
        origFile = f"{base}Base{ext}"
        if unstamp:
            label = "RESTORE"
            serverprint(f"STAMP: {label} {callFile}")
            copyfile(origFile, callFile)
            continue

        mapFile[origFile] = callFile
        (text, theseChanges, theseRemoves) = changedCallFiles(origFile)
        texts[origFile] = text
        for (fileFrom, fileTo) in theseChanges:
            changes.setdefault(origFile, set()).add(
                (fileFrom, fileTo)
            )
        removes |= theseRemoves

    for fileRem in sorted(removes):
        serverprint(f"STAMP: REMOVE {fileRem}")
        os.remove(fileRem)
    for (origFile, changedFiles) in changes.items():
        callText = texts[origFile]
        for (fileFrom, fileTo) in changedFiles:
            if fileFrom in changed:
                continue
            if not os.path.exists(fileTo):
                serverprint(f"STAMP: COPY {fileFrom} => {fileTo}")
                copyfile(fileFrom, fileTo)

            callText = callText.replace(fileFrom, fileTo)
            changed.add(fileFrom)

        callFile = mapFile[origFile]
        origCallText = None
        if os.path.exists(callFile):
            with open(callFile) as cf:
                origCallText = cf.read()
        if origCallText is None or origCallText != callText:
            label = "WRITE" if origCallText is None else "REWRITE"
            serverprint(f"STAMP: {label} {callFile}")
            with open(callFile, "w") as cf:
                cf.write(callText)


if __name__ == "__main__":
    main()
