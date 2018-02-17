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

        #obtain credentials, authenticate GDAX client and websocket, and then over-write credentials
        self._passphrase = ""
        self._secret = ""
        self._key = ""
        self.get_credentials(credentials_file="../../credentials.txt")      #fills in passphrase, secret, and key

        #main body parts
        self._client = gdax.AuthenticatedClient(self._key, self._secret, self._passphrase)
        self._socket = webSocket

        #other bot stuff
        self._name = name
        self._currency = currency
        self._running = False

        self.scramble_credentials()

    #####################
    ##---- GETTERS ----##
    #####################
    def name(self):
        return self._name

    def currency(self):
        return self._currency

    def socket(self):
        return self._socket

    def client(self):
        return self._client

    def running(self):
        self._running = self._running and not self.socket().stop
        return self._running

    #####################
    ##---- SETTERS ----##
    #####################
    def set_currency(self, product):
        print("New currency being traded: ", product)
        self._currency = product

    #Returns the amount of all holdings in your account including cash
    def get_balances(self, all_currencies=False):
        accounts = self.client().get_accounts()
        for account in accounts:
            currency = account["currency"]
            amount = float(account["balance"])
            if currency != "USD" and currency == "BTC":
                BTC = amount
            if currency != "USD" and currency == "BCH":
                BCH = amount
            if currency != "USD" and currency == "ETH":
                ETH = amount
            if currency != "USD" and currency == "LTC":
                LTC = amount
            if currency == "USD":
                USD = amount
            if currency in self.currency():
                crypto = amount

        if all_currencies == False:
            return USD, crypto
        else:
            return USD, BTC, BCH, ETH, LTC

    #Obtains GDAX credentials from a file and stores them as fields of the bot.
    #they will only be stored until everything has been verified, and then should
    #be cleared by calling the self.scramble_credentials() method
    def get_credentials(self, credentials_file=None):
        if credentials_file is None:
            yay = 0
            while yay == 0:
                file_loc = input("Drag and drop credential file here, or type path: ")
                try:
                    cred_file = open(file_loc)
                    yay = 1
                except:
                    print("Sorry, That file doesn't seem to exist. Please try again.")
                    yay = 0

        else:
            cred_file = open(credentials_file)

        lines = cred_file.readlines()
        self._passphrase = lines[0].split()[1]
        self._key = lines[1].split()[1]
        self._secret = lines[2].split()[1]
        cred_file.close()

    #We really shouldn't keep the credentials information around, so this method
    #over-writes the memory with information that is not useful.
    def scramble_credentials(self):
        self._passphrase = "Passphrase? What's that? I don't know what an API Passphrase is. Sorry, I think you got me confused with someone else"
        self._key = "Key? What's that? I don't know what an API Key is. Sorry, I think you got me confused with someone else"
        self._secret = "Secret? What's that? I don't know what an API Secret is. Sorry, I think you got me confused with someone else"

    #Starts the robot's listening and trading sequence
    def start(self, should_print=True):
        #self._data_center.create_portfolio()
        self._running = True
        self._socket.start()

        if should_print == True:
            print(self.name()+" has been started")

    #Stops the bot's trading sequence and ties up the trading thread
    def stop(self, should_print=True):
        self._running = False           #shut down client
        self.socket().close()           #shut down web socket.

        if should_print == True:
            print(self.name()+" has been stopped")
