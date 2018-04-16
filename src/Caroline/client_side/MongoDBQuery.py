"""
    Author: Nicholas Everhart

    This is the MongoDB Query operator. It will allow us to pull data within a given time stamp range
    of data stored within MongoDB.

    This data can then be manipulated based on the information we want to pull, edit, delete, or add.
"""

import sys
import gdax
from pymongo import MongoClient
from datetime import datetime, timedelta

################################################################################
#                                   Query                                      #
################################################################################
class DatabaseInterface:
	def __init__(self, user, password, db_name, db_IP):    	
		connection_str = "mongodb://{}:{}@{}/{}".format(user, password, db_IP, db_name)
		self._mongo_client = MongoClient(connection_str)
		self._db = self._mongo_client[db_name]

	def fetchTradesInRange(self, startDate, endDate, crypto):
		"""
		This function retrieves a collection of trades from our database.
		
		Input: beginning date, end date, and crypto currency.
				 * The crypto currency must be one of the following: BTC, BCH, ETH, or LTC
				 * The dates are formatted as such:  mm/dd/yyyy
			   More specific times are not supported and providing hours, minutes or seconds 
			   will result in an error.
			   
		Output: ?...
		"""
		start = datetime.strptime(startDate, '%m/%d/%Y').replace(hour=0, minute=0, second=0)
		end   = datetime.strptime(endDate, '%m/%d/%Y').replace(hour=23, minute=59, second=59)
		
		print("fetching trades from [{}] to [{}]...".format(start,end))
		
		cursor = self._db[crypto+"_matches"].find({"time": {"$gte": start, "$lte": end}});
		
		print(cursor.count())
		
		i=0
		for doc in cursor:
			print(i)
			i+=1
			print(doc)
		

		'''
		# Create the list of dictionaries (one dictionary per entry in the `trade` list)
		flattened_records = []
		for trade in cursor:
		    trade_id = trade['_id']
		    for trade in trade['time']:
		        flattened_record = {
		            '_id': trade_id,
		            'time': trade['time'],
		        }
		        flattened_records.append(flattened_record)

		# Iterate through the list of flattened records and write them to the csv file
		with open('trade.csv', 'w') as outfile:
		    fields = ['_id', 'time']
		    write = csv.DictWriter(outfile, fieldnames=fields)
		    write.writeheader()
		    for flattened_record in flattened_records:
		        write.writerow(flattened_record)
		'''
interface = DatabaseInterface("sam", "GoodVibrations_69", "cryptos", "192.168.0.23")
interface.fetchTradesInRange("03/01/2018","03/10/2018","BCH")
