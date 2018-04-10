"""
    Author: Nicholas Everhart

    This is the MongoDB Query operator. It will allow us to pull data within a given time stamp range
    of data stored within MongoDB.

    This data can then be manipulated based on the information we want to pull, edit, delete, or add.

    Currently, the query doesn't work because I'm not a great programmer like Sam!

"""

import sys
import gdax
from pymongo import MongoClient
from datetime import datetime, timedelta

################################################################################
#                                   Query                                      #
################################################################################
# class DataQuery():
#     def __init__(self, product=None, channels=None, should_print=True):
#         super(DataRetriever, self).__init__(products=product, channels=channels)
#
#         self._should_print = should_print
#
# 	    #get access to a mongo client with sam's credentials:
# 	    #username: sam
# 	    #password: GoodVibrations_69
# 	    #127.0.0.1 is local host meaning that our database is on this computer,
# 	    #and we only have access to the cryptos database
#         self._mongo_client = MongoClient("mongodb://sam:GoodVibrations_69@127.0.0.1/cryptos")
#         self._db = self._mongo_client.cryptos

def dateRange(self, startDate, endDate, crypto):

    startDate.setSeconds(0);
    startDate.setHours(0);
    startDate.setMinutes(0);

    var dateMidnight = new Date(startDate);
    dateMidnight.setHours(23);
    dateMidnight.setMinutes(59);
    dateMidnight.setSeconds(59);

    #start = db.cryptos.find({"createdAt" : { $gte : morning(startDate) }});
    #end = db.cryptos.find({"createdAt" : { $lte : dateScrapedMidnight(endDate) }});
    ### OR ###
    db.cryptos.find( { time: { $gte: morning(startDate), $lte: dateScrapedMidnight(endDate) } } );

    cursor = client.cryptos.find( {}, {'_id': 1}, { time: { $gte: morning(startDate), $lte: dateScrapedMidnight(endDate) } } )

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
