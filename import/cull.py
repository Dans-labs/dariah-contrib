"""Culling

This is a messy, one time task to cull the current contents
of the production database with contributions.

We have to strip the legacy and remove some frills in the data that have
been introduced accidentally.
"""

import sys
import collections
from datetime import datetime as dt

from pymongo import MongoClient
from bson.objectid import ObjectId


DATABASE = "dariah_restored"
DATABASE_PROD = "dariah"
MC = MongoClient()
DB = MC[DATABASE]


def info(x):
    sys.stdout.write("{}\n".format(x))


# get the users

allUsers = [doc for doc in DB.user.find()]
eppnMap = {doc["eppn"]: doc["_id"] for doc in allUsers}
userFields = {
    "creator": False,
    "editors": True,
    "reviewerE": False,
    "reviewerF": False,
}

# tweak a user

tweakUsers = [
    doc
    for doc in allUsers
    if doc["eppn"] == "PaulinRibbe@dariah.eu" and "name" not in doc
]
if tweakUsers:
    tweakUser = tweakUsers[0]
    DB.user.update_one(
        {"_id": tweakUser["_id"]},
        {"$set": {"firstName": "Paulin", "lastName": "Ribbe", "name": "Paulin Ribbe"}},
    )
    info(f"""Updated irregular user "Paulin Ribbe" """)
    allUsers = [doc for doc in DB.user.find()]

# Drop some stray contributions

for doc in DB.contrib.find({"title": "88milSMS"}):
    DB.contrib.delete_one({"_id": doc["_id"]})
    info(f"""Contrib deleted: "{doc["title"]}" """)

# get contribs and assessments
currentContribs = [doc for doc in DB.contrib.find() if not doc.get("isPristine", False)]
currentContribIds = {doc["_id"] for doc in currentContribs}
currentAssessments = [
    doc for doc in DB.assessment.find() if doc["contrib"] in currentContribIds
]
nCurrentAss = len(currentAssessments)
currentAssessmentIds = {doc["_id"] for doc in currentAssessments}

# Remove a legacy user from an editors field

frnc01 = "FRNC01"
frnc01Id = eppnMap.get(frnc01, None)

if frnc01Id:
    for doc in DB.contrib.find({"title": "NAKALA, a tool to expose research data"}):
        newValue = [u for u in doc.get("editors", []) if u != eppnMap[frnc01]]
        DB.contrib.update_one({"_id": doc["_id"]}, {"$set": {"editors": newValue}})
        info(f"""Editors changed: removed {frnc01} from "{doc["title"]}" """)

# Modify a stray score of "7 - " into "4 - complete" in every assesment that uses it,
# and gthen remove the "7 - score"

strayScoreId = ObjectId("5b44c1f0b5dbf5efda72fad7")
strayScores = list(DB.score.find({"_id": strayScoreId}))
if strayScores:
    strayScore = strayScores[0]
    strayStr = f"{strayScore.get('score', '??')} : {strayScore.get('level', '??')}"

    criteriaWithStrayScoreIds = list(
        doc["criteria"] for doc in DB.score.find({"_id": strayScoreId})
    )
    if criteriaWithStrayScoreIds:
        criteriaWithStrayScoreId = criteriaWithStrayScoreIds[0]
        criteriaWithStrayScores = list(
            DB.criteria.find({"_id": criteriaWithStrayScoreId})
        )
        if criteriaWithStrayScores:
            criteriaWithStrayScore = criteriaWithStrayScores[0]

            neighbourScores = list(
                DB.score.find({"criteria": criteriaWithStrayScoreId})
            )
            replaceScore = None
            for doc in neighbourScores:
                if doc["score"] == 4:
                    replaceScore = doc

            if replaceScore:
                replaceStr = (
                    f"{replaceScore.get('score', '??')} :"
                    f" {replaceScore.get('level', '??')}"
                )

                strayCriteriaEntries = list(
                    DB.criteriaEntry.find({"score": strayScoreId})
                )
                strayCriteriaEntryIds = {doc["_id"] for doc in strayCriteriaEntries}
                strayAssessments = {doc["assessment"] for doc in strayCriteriaEntries}

                tweakAssessments = {}
                for doc in currentAssessments:
                    if doc["_id"] in strayAssessments:
                        tweakAssessments[doc["_id"]] = doc["title"]

                replaceScoreId = replaceScore["_id"]
                for doc in strayCriteriaEntries:
                    title = tweakAssessments[doc["assessment"]]

                    DB.criteriaEntry.update_one(
                        {"_id": doc["_id"]}, {"$set": {"score": replaceScoreId}}
                    )
                    info(
                        f"""Changed score {strayStr} into {replaceStr}"""
                        f""" in assessment "{title}" """
                    )
    DB.score.delete_one({"_id": strayScoreId})
    info(f"Deleted stray score {strayStr}")

# Drop spurious tables

for table in """
    assessmentLegacy
    contrib_consolidated
    inGroup
    review_consolidated
""".strip().split():
    DB[table].drop()

allContribs = [doc for doc in DB.contrib.find()]
legacyContribs = [doc for doc in DB.contrib.find() if doc.get("isPristine", False)]
currentContribs = [doc for doc in DB.contrib.find() if not doc.get("isPristine", False)]

nAll = len(allContribs)
nLegacy = len(legacyContribs)
nCurrent = len(currentContribs)
ok = nAll == nLegacy + nCurrent

info(f"All contributions    : {nAll:>4}")
info(f"Legacy contributions : {nLegacy:>4}")
info(f"Current contributions: {nCurrent:>4}")
info("It adds up" if ok else "It does not add up!")

# Check that there are no legacy assessments, reviews, criteria entries, review entries
# N.B. We also check if there are dangling records: pointing to non-existent records

legacyContribIds = {doc["_id"] for doc in legacyContribs}
currentContribIds = {doc["_id"] for doc in currentContribs}

legacyAssessments = [
    doc for doc in DB.assessment.find() if doc["contrib"] in legacyContribIds
]
danglingAssessments = [
    doc for doc in DB.assessment.find() if doc["contrib"] not in currentContribIds
]
nLegacyAss = len(legacyAssessments)
nDanglingAss = len(danglingAssessments)

info(f"Current  assessments : {nCurrentAss:>4}")
info(f"Legacy   assessments : {nLegacyAss:>4}")
info(f"Dangling assessments : {nDanglingAss:>4}")

legacyReviews = [doc for doc in DB.review.find() if doc["contrib"] in legacyContribIds]
danglingReviews = [
    doc for doc in DB.review.find() if doc["contrib"] not in currentContribIds
]
currentReviews = [
    doc for doc in DB.review.find() if doc["contrib"] in currentContribIds
]
nCurrentReviews = len(currentReviews)
currentReviewIds = {doc["_id"] for doc in currentReviews}

nLegacyReviews = len(legacyReviews)
nDanglingReviews = len(danglingReviews)

info(f"Current  reviews : {nCurrentReviews:>4}")
info(f"Legacy   reviews : {nLegacyReviews:>4}")
info(f"Dangling reviews : {nDanglingReviews:>4}")

danglingCriteriaEntries = [
    doc
    for doc in DB.criteriaEntry.find()
    if doc["assessment"] not in currentAssessmentIds
]
nDanglingCriteriaEntries = len(danglingCriteriaEntries)

info(f"Dangling criteriaEntries : {nDanglingCriteriaEntries:>4}")

danglingReviewEntries = [
    doc for doc in DB.reviewEntry.find() if doc["review"] not in currentReviewIds
]
nDanglingReviewEntries = len(danglingReviewEntries)

info(f"Dangling reviewEntries : {nDanglingReviewEntries:>4}")

# There are no dangling or legacy assessments, reviews, criteriaEntries, reviewEntries
# Remove the legacy contributions

DB.contrib.delete_many({"_id": {"$in": list(legacyContribIds)}})
info(f"Deleted {len(legacyContribIds)} legacy contributions")

allContribs = [doc for doc in DB.contrib.find()]
nAll = len(allContribs)
info(f"All remaining contributions: {nAll:>4}")

# Change name of betaPackage into prodPackage and set the end date on 2030

betaPackages = list(DB.package.find({"title": "betaPackage"}))
if betaPackages:
    DB.package.update_one(
        {"title": "betaPackage"},
        {"$set": {"title": "productionPackage", "endDate": dt(2029, 12, 31, 23, 59, 59)}},
    )
    info(f"""Changed package name "betaPackage" into "productionPackage" """)

# Check the types of the contributions

# Delete other packages

for doc in DB.package.find():
    if doc["title"] == "productionPackage":
        continue
    else:
        DB.package.delete_one({"_id": doc["_id"]})
        info(f"Deleted legacy package: {doc['title']}")

typeInfo = {}
for doc in DB.typeContribution.find():
    typeName = " - ".join(x for x in [doc["mainType"], doc["subType"]] if x)
    typeInfo[doc["_id"]] = typeName

thePackage = list(DB.package.find())[0]
packageId = thePackage["_id"]
packageTypes = set(thePackage["typeContribution"])
legacyTypes = collections.defaultdict(collections.Counter)
for (docs, field, key) in [
    (allContribs, "typeContribution", "contrib"),
    (currentAssessments, "assessmentType", "assessment"),
    (currentReviews, "reviewType", "review"),
]:
    for doc in docs:
        typeContribution = doc.get(field, None)
        if typeContribution and typeContribution not in packageTypes:
            legacyTypes[typeContribution][key] += 1

info(f"Found {len(legacyTypes)} legacy type(s) in use.")
if legacyTypes:
    for (typeContribution, data) in sorted(legacyTypes.items()):
        for (k, n) in sorted(data.items()):
            info(f"in {n:>3} {k}(s): {typeInfo[typeContribution]}")

keepTypes = packageTypes | set(legacyTypes)

# Delete legacy types that do not occur

for doc in DB.typeContribution.find():
    if doc["_id"] in keepTypes:
        continue
    else:
        DB.typeContribution.delete_one({"_id": doc["_id"]})
        info(f"Deleted legacy type: {typeInfo[doc['_id']]}")

info(f"Keeping types:")
for doc in DB.typeContribution.find():
    info(f"{typeInfo[doc['_id']]}")

# Delete all criteria that are not linked to the production package

allCriteria = [doc for doc in DB.criteria.find()]
legacyCriteria = [doc for doc in DB.criteria.find() if doc["package"] != packageId]
currentCriteria = [doc for doc in DB.criteria.find() if doc["package"] == packageId]
currentCriteriaIds = {doc["_id"] for doc in currentCriteria}

info(f"All    criteria : {len(allCriteria):>4}")
info(f"Legacy criteria : {len(legacyCriteria):>4}")

for doc in DB.criteria.find():
    if doc["_id"] in currentCriteriaIds:
        continue
    else:
        DB.criteria.delete_one({"_id": doc["_id"]})
        info(f"Deleted legacy criteria: {doc['criterion']}")

allCriteria = [doc for doc in DB.criteria.find()]
allCriteriaIds = {doc["_id"] for doc in allCriteria}
info(f"{len(allCriteria)} criteria left")

# Delete all scores that are not linked to criterion

allScore = [doc for doc in DB.score.find()]
legacyScore = [
    doc for doc in DB.score.find() if doc.get("criteria", None) not in allCriteriaIds
]
currentScore = [
    doc for doc in DB.score.find() if doc.get("criteria", None) in allCriteriaIds
]
currentScoreIds = {doc["_id"] for doc in currentScore}

info(f"All    scores : {len(allScore):>4}")
info(f"Legacy scores : {len(legacyScore):>4}")

for doc in DB.score.find():
    if doc["_id"] in currentScoreIds:
        continue
    else:
        DB.score.delete_one({"_id": doc["_id"]})
        info(
            f"Deleted legacy score: {doc.get('level', '??')}"
            f" - {doc.get('score', '??')}"
        )


allScore = [doc for doc in DB.score.find()]
allScoreIds = {doc["_id"] for doc in allScore}
info(f"{len(allScore)} scores left")

occurringUsers = collections.defaultdict(list)
for table in """
    assessment
    contrib
    country
    criteria
    criteriaEntry
    decision
    discipline
    keyword
    package
    permissionGroup
    review
    reviewEntry
    score
    tadirahActivity
    tadirahObject
    tadirahTechnique
    typeContribution
    user
    vcc
    workflow
    year
""".strip().split():
    for doc in DB[table].find():
        for (field, multiple) in userFields.items():
            if multiple:
                for u in doc.get(field, []):
                    occurringUsers[u].append((table, doc, field))
            else:
                u = doc.get(field, None)
                if u:
                    occurringUsers[u].append((table, doc, field))

keepUsers = [
    doc
    for doc in allUsers
    if not doc.get("isPristine", False) or doc["_id"] in occurringUsers
]
legacyUsers = [
    doc
    for doc in allUsers
    if doc.get("isPristine", False) and doc["_id"] not in occurringUsers
]
info(f"{len(allUsers)} users in user table")
info(f"{len(legacyUsers)} legacy users")
info(f"{len(keepUsers)} occurring users to keep")
for (i, (label, users)) in enumerate(
    (("Keep users", keepUsers), ("Legacy users", legacyUsers),)
):
    info(label)
    collect = []
    for doc in users:
        occurrences = occurringUsers.get(doc["_id"], [])
        pristine = "" if doc.get("isPristine", False) else "*"
        fullName = doc.get("name", "")
        firstName = doc.get("firstName", "")
        lastName = doc.get("lastName", "")
        eppn = doc.get("eppn", "")
        name = fullName if fullName else " ".join(x for x in (firstName, lastName) if x)
        collect.append((f"{name} ({eppn})", pristine, len(occurrences)))
        if i == 1:
            DB.user.delete_one({"_id": doc["_id"]})
    for (name, pristine, n) in sorted(collect):
        if i == 1:
            info(f"Deleted legacy user {n:>3} {pristine}{name}")
        else:
            info(f"Kept user {n:>3} {pristine}{name}")
