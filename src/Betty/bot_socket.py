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
    def __init__(self, product=None, channels=None, should_print=True):
        super(BotSocket, self).__init__(products=product, channels=channels)
        
        self._should_print = should_print
        self._data_center = None
        self._history_size = 1000
        self._message_count = 0

    def on_open(self):
        if self._should_print:
            print("-- Starting Bot Socket --")
        self.stop = 0

    def on_message(self, msg):        
        if 'product_id' in msg and 'price' in msg and 'side' in msg and 'time' in msg and 'sequence' in msg and 'type' in msg and msg['type'] == 'match':
            self._message_count += 1
            msg["msg_type"] = "price_match"

            if self._should_print:
                print("{}   {}: {:10}\t{}".format(msg['time'], msg['product_id'], msg['price'], msg['side']))

            self._data_center.dispatch_message(msg)
                        
    def on_close(self):
        self.stop = 1
        if self._should_print:
            print("-- Terminating Bot Socket --")
            print("message count: " + str(self._message_count))
    
    def clear_history(self):    
        self._history = {"BTC-USD": [], "BCH-USD": [], "LTC-USD": [], "ETH-USD": []}
        
    def set_data_center(self, data_center):
        self._data_center = data_center
        self._message_count = 0
