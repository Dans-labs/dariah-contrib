import sys
import collections
from datetime import datetime as dt

from pymongo import MongoClient
from bson.objectid import ObjectId


DATABASE = "dariah_restored"
DB = MongoClient()[DATABASE]


def info(x):
    sys.stdout.write("{}\n".format(x))


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
currentAssessments = [
    doc for doc in DB.assessment.find() if doc["contrib"] in currentContribIds
]
nCurrentAss = len(currentAssessments)
currentAssessmentIds = {doc["_id"] for doc in currentAssessments}

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
allContribs = [doc for doc in DB.contrib.find()]
nAll = len(allContribs)
info(f"All remaining contributions: {nAll:>4}")

# Change name of betaPackage into prodPackage and set the end date on 2030

DB.package.update_one(
    {"title": "betaPackage"},
    {"$set": {"title": "productionPackage", "endDate": dt(2029, 12, 31, 23, 59, 59)}},
)

# Check the types of the contributions

# Delete other packages

for doc in DB.package.find():
    if doc["title"] == "productionPackage":
        continue
    else:
        DB.package.delete_one({"_id": doc["_id"]})

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

info(f"Found {len(legacyTypes)} legacy type(s):")
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

info("Keeping types:")
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

# Make a note of an outlier score (a later addition by Francesca Morselli)

strayScoreId = ObjectId("5b44c1f0b5dbf5efda72fad7")
strayScore = list(DB.score.find({"_id": strayScoreId}))[0]
info(
    f"Strange score: {strayScore.get('level', '??')} : {strayScore.get('score', '??')}"
)

criteriaOfStrayId = list(
    doc["criteria"] for doc in DB.score.find({"_id": strayScoreId})
)[0]
criteriaOfStray = list(DB.criteria.find({"_id": criteriaOfStrayId}))[0]
info(f"Criterion with a strange score:")
info(criteriaOfStray["criterion"])
info(criteriaOfStray["remarks"])

neighbourScores = list(DB.score.find({"criteria": criteriaOfStrayId}))
info("Scores for this criterion:")
for doc in neighbourScores:
    info(f"score: {doc.get('level', '??')} : {doc.get('score', '??')}")

strayCriteriaEntries = list(DB.criteriaEntry.find({"score": strayScoreId}))
info(f"{len(strayCriteriaEntries)} criteria entries use this score")
strayCriteriaEntryIds = {doc["_id"] for doc in strayCriteriaEntries}
strayAssessments = {doc["assessment"] for doc in strayCriteriaEntries}
info(f"{len(strayAssessments)} assessments use this score:")
for doc in currentAssessments:
    if doc["_id"] in strayAssessments:
        info(f"Strange score 7 used in: {doc['title']}")


allScore = [doc for doc in DB.score.find()]
allScoreIds = {doc["_id"] for doc in allScore}
info(f"{len(allScore)} scores left")

allUsers = [doc for doc in DB.user.find()]
eppnMap = {doc["eppn"]: doc["_id"] for doc in allUsers}
userFields = {
    "creator": False,
    "editors": True,
    "reviewerE": False,
    "reviewerF": False,
}
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
info(f"{len(allUsers)} in user table")
info(f"{len(legacyUsers)} legacy users")
info(f"{len(keepUsers)} occurring users to keep")
for (label, users) in (
    ("Keep users", keepUsers),
    ("Legacy users", legacyUsers),
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
    for (name, pristine, n) in sorted(collect):
        info(f"{n:>3} {pristine}{name}")

# note some users:

for eppn in ("CIO01", "FRNC01"):
    occs = occurringUsers[eppnMap[eppn]]
    info(f"{eppn}:")
    for (table, doc, field) in occs:
        info(f"{table}-{field} ({doc.get('title', doc.get('rep'))})")
        if eppn == "FRNC01":
            if field == "editors":
                newValue = [u for u in doc[field] if u != eppnMap[eppn]]
                DB[table].update_one({"_id": doc["_id"]}, {"$set": {field: newValue}})


tweakUser = [doc for doc in keepUsers if doc["eppn"] == "PaulinRibbe@dariah.eu"][0]
DB.user.update_one(
    {"_id": doc["_id"]},
    {"$set": {"firstName": "Paulin", "lastName": "Ribbe", "name": "Paulin Ribbe"}},
)

# determine for current contributions
#   the users involved in contribs, assessments, reviews, criteriaEntries,
#   reviewEntries, and all valueTables
#   also think of the editors fields, the reviewerEF fields
#   delete these users
#
# After running this: make a backup and restore it on the production system
