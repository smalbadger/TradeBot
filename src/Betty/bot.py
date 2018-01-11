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

import sys
import gdax
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
    def __init__(self, name="Bot", currency="BTC-USD", transition_buffer=0.4, webSocket=None):
        
        #obtain credentials, authenticate GDAX client and websocket, and then over-write credentials
        self._passphrase = ""
        self._secret = ""
        self._key = ""
        self.get_credentials(credentials_file="../../credentials.txt")      #fills in passphrase, secret, and key
        self._client = gdax.AuthenticatedClient(self._key, self._secret, self._passphrase)
        self._socket = webSocket
        self.scramble_credentials() #over-writes the credentials with new characters
        
        self._name = name
        self._fsm = FSM(state_usage=[3,4,5])
        self._currency = currency
        self._running = False
        self._calibration = False
        
        # These fields will only be used for fake trading analysis. Each bot will keep a portfolio
        # and at the end of program execution, we'll plot the bots against each other 
        self._prices_at_trading = []    #keeps the price history of the crypto at the trading points
        self._portfolio_at_trading = [] #keeps the value history of the bot's portfolio 
        self._crypto = 0                #set an initial value for fake crypto
        self._cash = float(self.client().get_product_ticker(product_id=self.currency())["price"])  #set an initial fake cash value

        

    #####################
    ##---- GETTERS ----##
    #####################
    def name(self):
        return self._name
        
    def calibration(self):
        return self._calibration    
        
    def currency(self):
        return self._currency
        
    def socket(self):
        return self._socket
        
    def client(self):
        return self._client
        
    def current_state():
        return self._fsm.current_state()
        
    def history_is_full(self):
        return len(self._socket._history) == self._socket._history_size
        
    def historical_prices(self, until_time=None):
        if until_time == None:
            return self._socket._history[self.currency()]
        else:
            history = []
            
            for i in self._socket._history[self.currency()]:
                if i["time"] != until_time:
                    history.append(i) 
                
            history.append(i) 
            return history
        
    def cash(self):
        return self._cash
        
    def crypto(self):
        return self._crypto
        
    def running(self):
        self._running = self._running and not self.socket().stop
        return self._running
        
    #returns the amount of crypto and the amount of cash that is available to the bot
    #Note, this method retrieves data directly from GDAX and is not to be confused 
    #with the cash and crypto fields of the bot.
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
    def start(self, should_print=True, calibration=False):
        self.create_portfolio()
        self._running = True
        self._calibration = calibration
        #if self.socket().stop: #only start the socket once
        self._socket.start()
        self._fsm.run(self, calibration=calibration)
        
        
        if should_print == True:
            print(self.name()+" has been started")

    #Stops the bot's trading sequence and ties up the trading thread
    def stop(self, should_print=True):
        self._running = False           #shut down client
        self._fsm._trade_thread.join()  #close trading thread
        self.socket().close()           #shut down web socket.
        
        if not self._calibration:
            #self.print_trade_history()
            self.create_portfolio()
            self.plot_session()
        
        if should_print == True:
            print(self.name()+" has been stopped")

    #This method just generates a portfolio donut chart using plotly. 
    #Currently, the picture gets put on their website
    def create_portfolio(self):
        prices = {}
        for i in self.client().get_products():
            p_id = i["id"]
            if "USD" in p_id:
                prices[p_id] = float(self.client().get_product_ticker(product_id=p_id)["price"])

        USD, BTC_amount, BCH_amount, ETH_amount, LTC_amount = self.get_balances(all_currencies=True)
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
                
    def print_price_history(self):
        #print all of th prices that were recorded in the history of the bot.
        history = self.historical_prices()
        for entry in history:
            print("sequence: {:d}   price: {:6.2f}   side: {}".format(entry['sequence'], entry['price'], entry['side']))
                
    def print_trade_history(self):
        prices = self._prices_at_trading
        portfolio = self._portfolio_at_trading
        
        assert (len(prices) == len(portfolio)), "OOPS: Somehow the trading history arrays were not built correctly."
        
        for i in range(len(prices)):
            print("portfolio: {:.2f}    price: {:.2f}".format(portfolio[i], prices[i]))
    
    def plot_session(self):
        #This method is mostly meant for debug purposes to see how the bot is doing against the crypto itself.
        #It relies on the _prices_at_trading and _profolio_at_trading lists being populated.
        #Note, this method may not be called if debug information is not gathered or the bot was not run.
        
        assert(len(self._prices_at_trading) != 0 and len(self._portfolio_at_trading)!=0)
        
        if len(self._prices_at_trading) != len(self._portfolio_at_trading):
            print("\n\nWARNING! price and portfolio histories are not the same length.")
            print("prices    length: {}".format(len(self._prices_at_trading)))
            print("portfolio length: {}".format(len(self._portfolio_at_trading)))
            print("Cannot generate session performance analysis.")
            print("\n\n")
            
                    
        #color_spectrum = cl.to_html( cl.scales['7']['div']['RdYlGn']
        #color_spectrum = []
        base_price = self._prices_at_trading[0]["value"]
        base_portfolio_value = self._portfolio_at_trading[0]["value"]
        
        x_axis = []
        portfolio_value_at_trading = self._portfolio_at_trading[:]
        portfolio_color_at_trading = self._portfolio_at_trading[:] 
        prices_at_trading = self._prices_at_trading[:]
        
        difference = []
        for i in range(len(self._prices_at_trading)):
            x_axis.append(i)
            portfolio_value_at_trading[i] = ((self._portfolio_at_trading[i]["value"] / base_portfolio_value) -1 ) * 100
            prices_at_trading[i] = ((self._prices_at_trading[i]["value"] / base_price) -1 )* 100
            
            difference.append(portfolio_value_at_trading[i] - prices_at_trading[i])
            
            #if self._portfolio_value_at_trading[i]["state"] != 0:
            #    portfolio_color_at_trading[i] = self._portfolio_value_at_trading[i]["state"] + 1
            #else:
            #    portfolio_color_at_trading[i] = self._portfolio_value_at_trading[i]["state"]
            
            
        trace1 = go.Scatter(
            x = x_axis,
            y = prices_at_trading,
            name = 'product',
            connectgaps = True
        )
        trace2 = go.Scatter(
            x = x_axis,
            y = portfolio_value_at_trading,
            name = 'portfolio',
            connectgaps = True
        )
        trace3 = go.Scatter(
            x = x_axis,
            y = difference,
            name = 'difference',
            connectgaps = True
        )

        data = [trace1, trace2, trace3]

        fig = dict(data=data)
        py.plot(fig, filename=(self.name()+"_results"))
