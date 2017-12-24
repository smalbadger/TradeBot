"""
    Author: Sam Badger
    
    This is the Bot class. The most important parts are:
        + self._client
            - Used to interact with the GDAX platform and user accounts. To do any trading, we need to use the 
              gdax.AuthenticatedClient() function. This gives access to functions that interact with a specific
              account, but requires that you provide an API key, secret, and passphrase.
        + self._socket
            - This will connect you to the websocket. The websocket allows you to get constant information. To 
              reduce thread usage, it's best to create a BotSocket object (my wrapper for the websocket) and pass
              it in to each of the Bot objects that you create.
              
    For simplicity, the Bot only supports trading one cryptocurrency. To trade multiple currencies, you should create 
    multiple bot objects with different currency attributes. Note that each bot will use its own thread for trading. 
    This is to prevent unnecessary delays in trading. SPAWNING TOO MANY BOTS WILL CRASH YOUR PROGRAM. Since the websocket
    also uses a thread, you should see how many threads you have on your computer (cores * threads) and spawn a maximum of 
    that number minus one bots. 
    
    I recommend not starting multiple bots that are trading the same cryptocurrency. Also, please note that the bot will
    default to trading bitocin if no other currency is given.
"""


import gdax
import sys
import time
from threading import Thread
import plotly
import plotly.plotly as py
import plotly.graph_objs as go

from bot_socket import BotSocket
from fsm import *

################################################################################
#                                   Bot                                        #
################################################################################
class Bot():
    def __init__(self, webSocket, name="Bot", currency="BTC-USD", transition_buffer=0.4):
        
        #obtain credentials, authenticate GDAX client and websocket, and then over-write credentials
        self._passphrase = ""
        self._secret = ""
        self._key = ""
        self.get_credentials()      #fills in passphrase, secret, and key
        self._client = gdax.AuthenticatedClient(self._key, self._secret, self._passphrase)
        self._socket = webSocket
        self.scramble_credentials() #over-writes the credentials with new characters
        
        self._name = name
        self._fsm = FSM(transition_buffer)
        self._currency = currency
        self._running = False
        
        # These fields will only be used for fake trading analysis. Each bot will keep a portfolio
        # and at the end of program execution, we'll plot the bots against each other 
        self._prices_at_trading = []    #keeps the price history of the crypto at the trading points
        self._portfolio_at_trading = [] #keeps the value history of the bot's portfolio 
        self._crypto = 0                #set an initial value for fake crypto
        self._cash = 14000              #set an initial fake cash value

        

    #####################
    ##---- GETTERS ----##
    #####################
    def name(self):
        return self._name
        
    def socket(self):
        return self._socket
        
    def client(self):
        return self._client
        
    def current_state():
        return self._fsm.current_state()
        
    def history_is_full(self):
        return len(self._socket._history) == self._socket._history_size
        
    def historical_prices(self):
        return self._socket._history
        
    def cash(self):
        return self._cash
        
    def crypto(self):
        return self._crypto
        
    def running(self):
        return self._running
        
    #returns the amount of crypto and the amount of cash that is available to the bot
    #Note, this method retrieves data directly from GDAX and is not to be confused 
    #with the cash and crypto fields of the bot.
    def get_balances(self):
        accounts = self.client().get_accounts()
        for account in accounts:
            currency = account["currency"]
            amount = float(account["balance"])
            if currency != "USD" and currency in self.currency():
                crypto = amount
            if currency == "USD":
                USD = amount
        return crypto, USD

    #Obtains GDAX credentials from a file and stores them as fields of the bot.
    #they will only be stored until everything has been verified, and then should 
    #be cleared by calling the self.scramble_credentials() method
    def get_credentials(self, credentials_file=None):
        if crredentials_file is None:
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
        self._running = True
        self._socket.start()
        #self._fsm.run(self)
        
        if should_print == True:
            print(self.name()+" has been started")

    #Stops the bot's trading sequence and ties up the trading thread
    def stop(self, should_print=True):
        self._running = False           #shut down client
        self._fsm._trade_thread.join()  #close trading thread
        self.socket().close()           #shut down web socket.
        
        if should_print == False:
            print(self.name()+" has been stopped")

    #This method just generates a portfolio donut chart using plotly. 
    #Currently, the picture gets put on their website
    def create_portfolio(self):
        prices = {}
        for i in self.client().get_products():
            p_id = i["id"]
            if "USD" in p_id:
                prices[p_id] = float(self.client().get_product_ticker(product_id=p_id)["price"])

        USD, BTC_amount, BCH_amount, ETH_amount, LTC_amount = self.get_balances()
        BTC_worth, BCH_worth, ETH_worth, LTC_worth = (BTC_amount * prices["BTC-USD"]), (BCH_amount * prices["BCH-USD"]), (ETH_amount * prices["ETH-USD"]), (LTC_amount * prices["LTC-USD"]),

        net_worth = USD + BTC_worth + BCH_worth + ETH_worth + LTC_worth
        net_worth = round(net_worth, 2)
        title = "GDAX\n${}".format(net_worth)

        plotly.tools.set_credentials_file(username='TradeBotTeam', api_key='SJTSXTDYHHtwLyul8olP')
        fig = {
            "data": [{
                 "values": [USD, BTC_worth, BCH_worth, ETH_worth, LTC_worth],
                 "labels": ["USD", "BTC", "BCH", "ETH", "LTC"],
                 "domain": {"x": [0, 1]},
                 "name"  : "Portfolio",
                 "hoverinfo": "label+percent+name",
                 "hole": .5,
                 "type": "pie"
             }],
             "layout": {
                 "title": "Portfolio",
                 "annotations": [{
                     "font": { "size": 20 },
                     "showarrow": False,
                     "text": title
                 }]
             }
        }

        pie_chart = py.plot(fig, filename="GDAX_porfolio_pie_chart")
        return pie_chart

    #This method uses the client object to print a list of all available crypto prices
    def print_current_prices(self):
        for i in self.client().get_products():
            p_id = i["id"]
            if "USD" in p_id:
                print(p_id + " : " + str(self.client().get_product_ticker(product_id=p_id)["price"]))
                
    #This method is mostly meant for debug purposes to see how the bot is doing against the crypto itself.
    #It relies on the _prices_at_trading and _profolio_at_trading lists being populated.
    #Note, this method may not be called if debug information is not gathered or the bot was not run. 
    def plot_session(self):
        x_axis = []
        for i in range(len(self._price_at_trade)):
            x_axis.append(i)
            
        trace1 = go.Scatter(
            x = x_axis,
            y = self._prices_at_trading,
            name = 'crypto price',
            connectgaps = True
        )
        trace2 = go.Scatter(
            x = x_axis,
            y = self._portfolio_at_trading,
            name = 'portfolio value',
            connectgaps = True
        )

        data = [trace1, trace2]

        fig = dict(data=data)
        py.plot(fig, filename=(self.name()+"_results"))
