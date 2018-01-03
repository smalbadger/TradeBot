"""
    Author: Sam Badger
    
    This is the BotSocket class. It's really just a wrapper for the gdax.WebsocketClient class.
    Creating this wrapper allows us to do whatever we want with the data coming in.
    
    The gdax websocket is used to get constant product information. There are also specific channels
    that you can subscribe to. Just go to the official gdax documentation to see them. 
    
    Currently, the BotSocket just takes all of the product prices once orders have been completed and 
    puts the information into arrays. There is a history dictionary with an array of each product so 
    that each bot can access only the information of the product it's interested in.
    
    Note that the on_open, on_message, and on_close methods are all methods of the WebsocketClient, but
    we are over-writing them. These are the only methods that can be over written from the WebsocketClient,
    but feel free to create your own additional methods and member variables
"""

import sys
import gdax

################################################################################
#                                 BotSocket                                    #
################################################################################
class BotSocket(gdax.WebsocketClient):
    def __init__(self, product=None, key=None, secret=None, passphrase=None, channels=None):
        super(BotSocket, self).__init__(products=product, api_key=key, api_secret=secret, api_passphrase=passphrase, channels=channels)
        self._history_size = 1000
        self._history = {"BTC-USD": [], "BCH-USD": [], "LTC-USD": [], "ETH-USD": []}
        self._message_count = 0

    def on_open(self):
        print("-- Starting Bot Socket --")
        self._history = {"BTC-USD": [], "BCH-USD": [], "LTC-USD": [], "ETH-USD": []}
        self._message_count = 0
        self.stop = 0

    def on_message(self, msg):
        self._message_count += 1
        
        if 'product_id' in msg and 'price' in msg and 'side' in msg and 'type' in msg and msg['type'] == 'match' and 'time' in msg and 'sequence' in msg:
            i = 0
            length = len(self._history[msg['product_id']])
            while length != 0 and msg['sequence'] < self._history[msg['product_id']][length-i-1]["sequence"]:
                i = i + 1
            product_id =   str(msg['product_id'])
            price      = float(msg['price'     ])
            side       =   str(msg['side'      ])
            time       =   str(msg['time'      ])
            sequence   =   int(msg['sequence'  ])
            if i == 0:
                self._history[msg['product_id']].append({"price": price, "side": side, "time": time, "sequence": sequence})
            else:
                self._history[msg['product_id']].insert(length-i, {"price": price, "side": side, "time": time, "sequence": sequence})
            
            print("{}: {:10.2f}\t{}".format(product_id, price, side))
            
    def on_close(self):
        self.stop = 1
        print("-- Terminating Bot Socket --")
        print("message count: " + str(self._message_count))
