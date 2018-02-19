"""
    Author: Sam Badger

"""

import sys
import gdax
import time
from threading import Thread

from bot_socket import BotSocket

################################################################################
#                                   Bot                                        #
################################################################################
class Bot():
    def __init__(self, name="Bot", currency="BTC-USD", webSocket=None):
        self._socket = webSocket

    #Starts the robot's listening and trading sequence
    def start(self, should_print=True):
        self._socket.start()

    #Stops the bot's trading sequence and ties up the trading thread
    def stop(self, should_print=True):
        self.socket().close()
