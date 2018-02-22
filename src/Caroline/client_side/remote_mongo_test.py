import pymongo
from getpass import getpass

username = input("Username: ")
password = getpass()

successful_login = True
client = pymongo.MongoClient("mongodb://{}:{}@192.168.0.23/cryptos".format(username, password))

db = client.cryptos

doc = db.BCH_matches.find_one()
print(doc["_id"].generation_time)
for field in doc:
    print(doc[field])
print(db.BCH_matches.count())
