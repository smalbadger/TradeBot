"""
    Authors: Nicholas Everhart and Sam Badger
	Date Created: April 16, 2018
"""

import sys
import gdax
import csv
from pymongo import MongoClient
from datetime import datetime, timedelta

################################################################################
#                                   Query                                      #
################################################################################
class DatabaseInterface:
	"""Interface with the cryptocurrency database"""
	
	def __init__(self, user, password, db_name, db_IP):    	
		"""
		Creates a DatabaseInterface object.
		This stores:
			* the mongo client
			* the cryptos database.
		"""
		connection_str = "mongodb://{}:{}@{}/{}".format(user, password, db_IP, db_name)
		self._mongo_client = MongoClient(connection_str)
		self._db = self._mongo_client[db_name]

	
	def fetchTradesInRange(self, startDate, endDate, crypto, csvWrite=True):
		"""
		Retrieves a collection of trades from our database.
		
		Input: 
		beginning date, end date, and crypto currency.
			* The crypto currency must be one of the following: BTC, BCH, ETH, or LTC
			* The dates are formatted as such:  mm/dd/yyyy
		More specific times are not supported and providing hours, minutes or seconds 
		will result in an error.
				   
		Output:
		Will either write trades to a csv file and return none OR it will not write to 
		a file and will return a list of dictionaries. each element in the list is a trade.
		"""
		start = datetime.strptime(startDate, '%m/%d/%Y').replace(hour=0, minute=0, second=0)
		end   = datetime.strptime(endDate, '%m/%d/%Y').replace(hour=23, minute=59, second=59)
		
		print("Fetching trades from [{}] to [{}]...".format(start,end))
		cursor = self._db[crypto+"_matches"].find({"time": {"$gte": start, "$lte": end}});
		print("There are", cursor.count(), "documents.")
		filename = start.strftime("%d-%b-%Y") + "_" + end.strftime("%d-%b-%Y") + ".csv"
		
		
		if csvWrite:
			with open(filename, 'w') as csvFile:
				fieldNames = list(cursor[0].keys())
				fieldNames.sort()
				writer = csv.DictWriter(csvFile, fieldnames=fieldNames)
				writer.writeheader()
				for doc in cursor:
					writer.writerow(doc)
		else:
			return list(cursor) 

# if this file is ran as a stand-alone module, we'll instantiate a 
if __name__ == "__main__":
	interface = DatabaseInterface("sam", "GoodVibrations_69", "cryptos", "192.168.0.23")
	interface.fetchTradesInRange("01/01/2018","04/16/2018","BCH")
