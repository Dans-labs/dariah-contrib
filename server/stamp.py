"""Tweak the inclusion of CSS and JS files.

An HTML file that is served on the web, and that references stylesheets and
scripts, will end up getting them from the browser cache in most cases.

Fact of life: if the developer changes the Javascript or stylesheet, most browser
do not see it, because they still fetch the old files from cache.

It is tedious to notify your users to do a so-called hard-refresh. The command is
different for different browsers, the concept is not widely known, and the effect is not
always guaranteed.

It is also clumsy to set a time-out on the cached files. After a fix, you want
to see the effect immediately. And if nothing has changed, there is no reason to
invalidate the cache on a regular basis.

Here we copy the files: we add a *slug* after the base name of the file, where
the slug is a series of digits, based on the modification time of the file.

Before shipping the html template file(s) and the stylesheets and scripts,
we make a copy of all stylesheets and scripts with a *slugged* name, and we let
the templates reference those files by their slugged counterparts.

!!! hint "Calling stamp.py"
    There are two ways to call this module on the command line:

    ```python3 stamp.py```

    Treats all relevant files with a slug, and takes care that all templates
    cll them by their slugged copies.

    ```python3 stamp.py un```

    Changes all template files back so that they call the unslugged versions
    of stylesheets and scripts.

!!! caution "Manual editing"
    Only edit the unslugged files.
    As for templates: only edit the template that end in `Base`, as in
    `indexBase.html`. The version that will call the slugged files is generated
    from this when `stamp.py` runs and saved as `index.html`.
"""

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
