import gdax
import sys
import time
import plotly
import plotly.plotly as py
import plotly.graph_objs as go


################################################################################
#                                 STATE                                        #
################################################################################
class state():
    """
        This class contains information for a single state of the finite state machine.
    """
    def __init__(self, name, next, prev):
        self._name = name
        self._transaction_percent = 5
        self._next = next
        self._prev = prev
        self._low = 1000000000
        self._high = 0
        self._upper_threshold = 0
        self._lower_threshold = 0
        self._entry = 0
    
    ##---- GETTERS ----##
    def next(self):
        return self._next
    def prev(self):
        return self._prev
    def percent(self):
        return self._transaction_percent
    def name(self):
        return self._name
    def entry(self):
        return self._entry
    def thresholds(self):
        return {"upper": self._upper_threshold, "lower":self._lower_threshold, "high": self._high, "low": self._low}

    def update_percent(self, new_percent):
        """
            This method updates the transaction percent for a state.
        """
        self._transaction_percent = new_percent
    
    def trade(self, bot):
        """
           This method initiates a trade. Each state will make a trade, except for the hold state. 
        """
        if "buy" in self._name:
            side = "buy"
        elif "sell" in self._name:
            side = "sell"
        else:
            return
        # product =
        # price =
        # order_type = "limit"
        crypto, cash = bot.product_pool()
        if side == "buy":
            size = (cash * (self._transaction_percent/100))/price
        elif side == "sell":
            size = crypto * (self._transaction_percent/100)


################################################################################
#                           FINITE STATE MACHINE                               #
################################################################################
class FSM():
    def __init__(self):
        """
            This is the finite state machine that we'll be using to decide if we should buy or sell.
            It has 6 states, 5 of which will be frequently visited.
            "Critical-Sell" - Emergency state to dump all. This is a failsafe that hopefully will never be visited.
            - Can only be visited by an extreme rate of price drop and the price being below 50% of the high
            
            "Strong-Sell"   - sell a specific amount of holdings every specific amount of time
            "Weak-Sell"     - sell a specific amount of holdings every specific amount of time
            "Hold"          - We don't know what to do at this point, so we won't do anything.
            "Weak-Buy"      - buy a specific amount of holdings every specific amount of time
            "Strong-Buy"    - buy a specific amount of holdings every specific amount of time
            
            the run() method will be used to start trading and state transitions.
        """
        CS = state("Critical-Sell", None, None)
        SS = state("Strong-Sell", None, None)
        WS = state("Weak-Sell", None, None)
        H = state("Hold", None, None)
        WB = state("Weak-Buy", None, None)
        SB = state("Strong-Buy", None, None)

        CS._next = SS
        SS._next = WS
        WS._next = H
        H._next = WB
        WB._next = SB

        SB._prev = WB
        WB._prev = H
        H._prev = WS
        WS._prev = SS
        SS._prev = CS

        H.update_percent(0)
        SS.update_percent(10)
        SB.update_percent(10)
        CS.update_percent(50)

        self._current_state = H
        self._transition_buffer = .1

    def current_state(self):
        return self._current_state

    def change_state(self, history):
        """
            This method is used to change states. It must be given an up-to-date history of prices
            where the last element in the list is the newest. Contains logic to decide if we should move
            toward buy, toward sell, or stay at the same state.
        """
        if len(history) == 0:
            return
        
        cur_state = self.current_state()
        thresh = cur_state.thresholds()
        
        last_price = history[-1]
        
        if "Sell" in cur_state.name():
            type = "sell"
        elif "Buy" in cur_state.name():
            type = "buy"
        elif "Hold" in cur_state.name():
            type = "hold"

        if last_price > thresh["high"]:
            cur_state.set_high(last_price)
        if last_price < thresh["low"]:
            cur_state.set_low(last_price)
        
        #FIXME: The conditions to change states below are wrong and need to be though out better
        #move towards buy
        if last_price >= cur_state.entry() + (cur_state.entry() * self._transition_buffer/100):
            if(current_state.next() != None):
                self._current_state = current_state.next()
                self._entry = last_price
        
        #move towards sell
        if last_price <= cur_state.entry() - (cur_state.entry() * self._transition_buffer/100):
            if(current_state.prev() != None):
                self._current_state = current_state.prev()
                self._entry = last_price
            
    def run(self, robot):
        """
            first checks to see if we need to change states, then makes the trade and updates the portfolio.
            we sleep for a short amount of time so we don't get blocked. (max server requests per second = 3)
        """
        #while robot.status():
        self.change_state(robot.historical_prices())
        self._current_state.trade(robot)
        robot.create_portfolio()
        
        time.sleep(30)

        print(robot.historical_prices())

################################################################################
#                                 BotSocket                                    #
################################################################################
class BotSocket(gdax.WebsocketClient):
    def __init__(self, product, key, secret, passphrase):
        super(BotSocket, self).__init__(products=product)
        self._history_size = 100000
        self._history = []
        self._message_count = 0
        
    def on_open(self):
        print("-- Starting Bot Socket --")
        self._history = []
        self._message_count = 0
        self.stop = 0
        
    def on_message(self, msg):
        self._message_count += 1
        if 'price' in msg and 'type' in msg:
            print ("Message type:", msg["type"], "\t@ {:.3f}".format(float(msg["price"])))
            if msg["type"] == "done":   #a "done" message means that the it's being traded at that price.
                if len(self._history) >= self._history_size:
                    self._history = self._history[1:].append(msg["price"])

    def on_close(self):
        print("-- Terminating Bot Socket --")
        self.stop = 1


################################################################################
#                                   Bot                                        #
################################################################################
class Bot():
    def __init__(self, currency):
        """
           This is the actual Bot. It contains account information including a client object needed to interact with GDAX.
        """
        self._passphrase = ""
        self._secret = ""
        self._key = ""
        self.get_credentials()
        self._client = gdax.AuthenticatedClient(self._key, self._secret, self._passphrase)
        self._socket = BotSocket(product=currency, key=self._key, secret=self._secret, passphrase=self._passphrase)
        self._fsm = FSM()
        self._currency = currency
        self._running = False
        self._crypto = 0
        self._cash = 0
    
        self.scramble_credentials()

    ##---- GETTERS ----##
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
    def product_pool(self):
        return self._crypto, self._cash
    def status(self):
        return self._running
    def get_balances(self):
        accounts = self.client().get_accounts()
        for account in accounts:
            currency = account["currency"]
            amount = float(account["balance"])
            if currency == "USD":
                USD = amount
            elif currency == "BTC":
                BTC = amount
            elif currency == "LTC":
                LTC = amount
            elif currency == "ETH":
                ETH = amount
            elif currency == "BCH":
                BCH = amount
            else:
                print("Unkown currency " + currency)
        return USD, BTC, BCH, ETH, LTC
    
    def get_credentials(self):
        yay = 0
        while yay == 0:
            file_loc = input("Drag and drop credential file here, or type path: ")
            try:
                cred_file = open(file_loc)
                yay = 1
            except:
                print("Sorry, That file doesn't seem to exist. Please try again.")
                yay = 0

        lines = cred_file.readlines()
        self._passphrase = lines[0].split()[1]
        self._key = lines[1].split()[1]
        self._secret = lines[2].split()[1]
        cred_file.close()
                    
    def scramble_credentials(self):
        """
           It isn't a good idea to store sensitive information if you don't have to, so we'll just over-write it all. 
        """
        self._passphrase = "Passphrase? What's that? I don't know what an API Passphrase is. Sorry, I think you got me confused with someone else"
        self._key = "Key? What's that? I don't know what an API Key is. Sorry, I think you got me confused with someone else"
        self._secret = "Secret? What's that? I don't know what an API Secret is. Sorry, I think you got me confused with someone else"

    def start(self):
        self._running = True
        self._socket.start()
        ### This will spawn another thread (once I learn how that works) that continuously trades.
        ### The condition to run will look like "while self._running: (trade)"
        self._fsm.run(self)
    
    def stop(self):
        self._running = False   #shut down client
        self.socket().close()   #shut down web socket.
    
    def update_historic_prices(self, new):
        #This will change. I don't actually want to update the whole list,
        #I just want to put new values at the front of it and take values off the end
        #so that we don't use too much memory.
        self._historic_prices = new

    def create_portfolio(self):
        """
           This method creates a cool donut chart showing total protfolio value and asset ditribution.
           TODO: figure out how to import it into a GUI application
        """
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

    def print_current_prices(self):
        for i in self.client().get_products():
            p_id = i["id"]
            if "USD" in p_id:
                print(p_id + " : " + str(self.client().get_product_ticker(product_id=p_id)["price"]))

def main():
    BitBot = Bot("BTC-USD")
    BitBot.start()
    BitBot.stop()
    BitBot.print_current_prices()

main()
