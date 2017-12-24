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

import gdax

################################################################################
#                                 BotSocket                                    #
################################################################################
class BotSocket(gdax.WebsocketClient):
    def __init__(self, product, key, secret, passphrase, channels):
        super(BotSocket, self).__init__(products=product, channels=channels)
        self._history_size = 1000
        self._history = {"BTC-USD": [], "BCH-USD": [], "LTC-USD": [], "ETH-USD": []}
        self._message_count = 0

    def on_open(self):
        print("-- Starting Bot Socket --")
        self._history = {"BTC-USD": [], "BCH-USD": [], "LTC-USD": [], "ETH-USD": []}
        self._message_count = 0
        self.stop = 0

    def on_message(self, msg):
        """
            FIXME: put each product in its corresponding array in the dictionary
        """
        self._message_count += 1
        print(msg)
        """
        if 'price' in msg and 'type' in msg:
            if msg["type"] == "done":   #a "done" message means that the it's being traded at that price.
                print ("Message type:", msg["type"], "\t@ {:.3f}".format(float(msg["price"])))
                if len(self._history) >= self._history_size:
                    self._history = (self._history[1:]).append(float(msg["price"]))
                else:
                    self._history.append(float(msg["price"]))
        """
        
    def on_close(self):
        self.stop = 1
        self.thread.join()
        print("-- Terminating Bot Socket --")
        print("message count: " + str(self._message_count))
