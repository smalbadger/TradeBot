import pymongo
from getpass import getpass
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

#username = input("Username: ")
#password = getpass()
db = 'cryptos'

successful_login = True
client = pymongo.MongoClient("mongodb://sam:GoodVibrations_69@192.168.0.23/cryptos")
#client = pymongo.MongoClient("mongodb://{}:{}@192.168.0.23/{}".format(username, password,db))

db = client.cryptos

for collection_name in db.collection_names():
    print(collection_name)
    print('\t{} documents'.format(db[collection_name].count()))

prices = []
times = []

time_delta = timedelta(minutes = 1)
docs = db.BCH_matches.find()

start_time = docs[0]["time"]
avg_price = 0
count = 0
for doc in docs:
    if (doc["time"] - start_time) < time_delta:
        #add on to current average
        avg_price += float(doc["price"])
        count += 1
        
    else:
        #tie up current average
        avg_price /= count
        prices.append(avg_price)
        times.append(start_time)
        #print("{} : {}".format(start_time, avg_price))
        
        #start new average
        start_time = doc["time"]
        avg_price = float(doc["price"])
        count = 1

plt.plot(times, prices)
plt.gcf().autofmt_xdate()
plt.show()
