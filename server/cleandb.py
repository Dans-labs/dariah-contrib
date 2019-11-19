from pymongo import MongoClient

USER_TABLES = {'contrib', 'assessment', 'review', 'criteriaEntry', 'reviewEntry'}


MONGO = MongoClient()
myDb = MONGO.dariah_clean

for table in USER_TABLES:
    myDb[table].drop()
