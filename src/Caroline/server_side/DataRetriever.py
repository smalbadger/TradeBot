"""
    Author: Sam Badger

    This is the BotSocket class. It's really just a wrapper for the gdax.WebsocketClient 
    class. Creating this wrapper allows us to do whatever we want with the data coming in.
    The gdax websocket is used to get constant product information. There are also specific 
    channels that you can subscribe to. Just go to the official gdax documentation to see 
    them.

    Currently, the BotSocket just takes all of the product prices once orders have been 
    completed and puts the information into arrays. There is a history dictionary with an 
    array of each product so that each bot can access only the information of the product 
    it's interested in.

    Note that the on_open, on_message, and on_close methods are all methods of the 
    WebsocketClient, but we are over-writing them. These are the only methods that can be 
    over written from the WebsocketClient,
    but feel free to create your own additional methods and member variables
"""

import sys
import gdax
from pymongo import MongoClient
from datetime import datetime, timedelta

################################################################################
#                                 BotSocket                                    #
################################################################################
class DataRetriever(gdax.WebsocketClient):
    def __init__(self, product=None, channels=None, should_print=True):
        super(DataRetriever, self).__init__(products=product, channels=channels)

        self._should_print = should_print

	    #create a mongo client with sam's credentials:
	    #username: sam
	    #password: GoodVibrations_69
	    #127.0.0.1 is local host meaning that our database is on this computer, 
	    #and we only have access to the cryptos database
        self._mongo_client = MongoClient("mongodb://sam:GoodVibrations_69@127.0.0.1/cryptos")
        self._db = self._mongo_client.cryptos


    def on_open(self):
        if self._should_print:
            print("-- Starting Bot Socket --")
        self.stop = 0

    def on_message(self, msg):
        if 'product_id' in msg and 'price' in msg and 'side' in msg and 'time' in msg and 'sequence' in msg and 'type' in msg and msg['type'] == 'match':

            new_date_str = msg['time'][0:-1]
            new_date_str = new_date_str[:10] + " " + new_date_str[11:-7]
            modified_time = datetime.strptime(new_date_str, '%Y-%m-%d %H:%M:%S')

            new_msg = {'price':msg['price'], 'side':msg['side'], 'time':modified_time, 'sequence':msg['sequence'], 'type':msg['type']}
            self._db[msg['product_id'][:3]+"_matches"].insert_one(new_msg)
            if self._should_print:
                print("{}   {}: {:10}\t{}".format(msg['time'], msg['product_id'], msg['price'], msg['side']))

    def on_close(self):
        self.stop = 1
        if self._should_print:
            print("-- Terminating Bot Socket --")

    def clear_history(self):
        self._history = {"BTC-USD": [], "BCH-USD": [], "LTC-USD": [], "ETH-USD": []}

if __name__ == "__main__":
    dr = DataRetriever(product=["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"], channels=["matches"])
dr.start()
