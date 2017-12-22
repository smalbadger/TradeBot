import gdax
import sys
import time
from threading import Thread
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
        self._low = 10000000
        self._high = 0
        self._upper_threshold = 0   #currently not using this
        self._lower_threshold = 0   #currently not using this
        self._entry = 0

        if "Sell" in name:
            self._transaction_type = "sell"
        elif "Buy" in name:
            self._transaction_type = "buy"
        elif "Hold" in name:
            self._transaction_type = "hold"

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


    def set_high(self, new_high):
        self._high = new_high
		
    def set_low(self, new_low):
        self._low = new_low
		
    def update_percent(self, new_percent):
        """
            This method updates the transaction percent for a state.
        """
        self._transaction_percent = new_percent

    def trade(self, bot):
        """
           This method initiates a trade. Each state will make a trade, except for the hold state.
        """
        if "Buy" in self._name:
            side = "buy"
        elif "Sell" in self._name:
            side = "sell"
        else:
            return
            
        available_cash = bot.cash()
        available_crypto = bot.crypto()
        price = bot.historical_prices()[-1]
        
        if side == "buy":
            transaction_cash_value = available_cash * self.percent() / 100
            fees = transaction_cash_value * .003 #assume that we'll always get charged the .3% buy fee.
            transaction_crypto_size = transaction_cash_value / price
            
            bot._cash = bot.cash() - transaction_cash_value - fees
            bot._crypto = bot.crypto() + transaction_crypto_size
            
        elif side == "sell":
            transaction_crypto_size = available_crypto * self.percent() / 100
            transaction_cash_value = price * transaction_crypto_size
            
            bot._cash = bot.cash() + transaction_cash_value
            bot._crypto = bot.crypto() - transaction_crypto_size
            
        bot._price_at_trade.append(price)
        bot._history_of_portfolio_value.append(bot.cash() + bot.crypto() * price)

################################################################################
#                           FINITE STATE MACHINE                               #
################################################################################
class FSM():
    def __init__(self, transition_buffer):
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
        WS.update_percent(15)
        WB.update_percent(15)
        SS.update_percent(30)
        SB.update_percent(30)
        CS.update_percent(50)

        self._current_state = H
        self._transition_buffer = transition_buffer
        self._trade_thread = None
        self._state_log = open("state_log.txt", "w")

    def current_state(self):
        return self._current_state

    def change_state(self, history):
        """
            This method is used to change states. It must be given an up-to-date history of prices
            where the last element in the list is the newest. Contains logic to decide if we should move
            toward buy, toward sell, or stay at the same state.
        """
        if len(history) == 0 or history[-1] == 0:
            return

        last_price = history[-1]

        cur_state = self.current_state()
        thresh = cur_state.thresholds()

        high = thresh["high"]
        low = thresh["low"]

        entry = cur_state.entry()
        if entry == 0:
            cur_state._entry = last_price
            entry = last_price
            
        #For debugging purposes
        #print("State: ", cur_state.name(), "\tentry: ", cur_state.entry(), "\tlast price: ", last_price)

        #update high and low
        if last_price > high:
            cur_state.set_high(last_price)
            high = last_price
        if last_price < low:
            cur_state.set_low(last_price)
            low = last_price

        next_state = cur_state

        #Decide if the bot should change states
        if cur_state.name() == "Strong-Buy":
            if last_price < (high - high * self._transition_buffer/100):
                next_state = cur_state.prev()

        elif cur_state.name() == "Weak-Buy":
            if last_price < (entry - entry * (self._transition_buffer/100)):
                next_state = cur_state.prev()
            #elif last_price > (entry + entry * self._transition_buffer/100):
            #    next_state = cur_state.next()
        
        elif cur_state.name() == "Hold":
            if last_price < (entry - entry * (self._transition_buffer/100)):
                next_state = cur_state.prev()
            elif last_price > (entry + entry * self._transition_buffer/100):
                next_state = cur_state.next()
        
        elif cur_state.name() == "Weak-Sell":
            #if last_price < (entry - entry * (self._transition_buffer/100)):
            #    next_state = cur_state.prev()
            if last_price > (entry + entry * self._transition_buffer/100):
                next_state = cur_state.next()

        elif cur_state.name() == "Strong-Sell":
            if last_price > (low + low * self._transition_buffer/100):
                next_state = cur_state.next()
            elif last_price < (entry*.9):  #only move to critical sell if the price decreases 10% after reaching strong sell state
                next_state = cur_state.prev()

        elif cur_state.name() == "Critical-Sell":
            if last_price > (low + low * self._transition_buffer/100):
                next_state = cur_state.next()

        else:
            print("ERROR: bot is at unknown state. Please check the logs.")
            sys.exit(1)
        
        if last_price != 0 and cur_state.entry() != 0:
            message = cur_state.name() + " -> " + next_state.name() + "\tentry price: " + str(cur_state.entry()) + "\tpercent change: " + str(round((last_price - cur_state.entry())/cur_state.entry(), 2)) + "%\n"
            #self._state_log.write(message)
            #print(message)
            
        if next_state != cur_state:
            next_state._entry = last_price
            
        self._current_state = next_state
        

    def run(self, robot):
        """
            first checks to see if we need to change states, then makes the trade and updates the portfolio.
            we sleep for a short amount of time so we don't get blocked. (max server requests per second = 3)
        """
        def _trade_routine():
            while robot._running:
                self.change_state(robot.historical_prices())
                self._current_state.trade(robot)
                time.sleep(.5)
            self._state_log.close()
            #robot.create_portfolio()

        self._trade_thread = Thread(target=_trade_routine)
        self._trade_thread.start()

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
        #print("-- Starting Bot Socket --")
        self._history = []
        self._message_count = 0
        self.stop = 0

    def on_message(self, msg):
        self._message_count += 1
        if 'price' in msg and 'type' in msg:
            if msg["type"] == "done":   #a "done" message means that the it's being traded at that price.
                #print ("Message type:", msg["type"], "\t@ {:.3f}".format(float(msg["price"])))
                if len(self._history) >= self._history_size:
                    self._history = (self._history[1:]).append(float(msg["price"]))
                else:
                    self._history.append(float(msg["price"]))

    def on_close(self):
        self.stop = 1
        self.thread.join()
        #print("-- Terminating Bot Socket --")
        #print("message count: " + str(self._message_count))

################################################################################
#                                   Bot                                        #
################################################################################
class Bot():
    def __init__(self, name, currency, transition_buffer, webSocket):
        """
           This is the actual Bot. It contains account information including a client object needed to interact with GDAX.
        """
        self._name = name
        self._passphrase = ""
        self._secret = ""
        self._key = ""
        self.get_credentials()
        self._client = gdax.AuthenticatedClient(self._key, self._secret, self._passphrase)
        self._socket = webSocket
        self._fsm = FSM(transition_buffer)
        self._currency = currency
        self._running = False
        self._crypto = 0
        self._cash = 13400
        self._price_at_trade = []
        self._history_of_portfolio_value = []

        self.scramble_credentials()

    ##---- GETTERS ----##
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
        """
        yay = 0
        while yay == 0:
            file_loc = input("Drag and drop credential file here, or type path: ")
            try:
                cred_file = open(file_loc)
                yay = 1
            except:
                print("Sorry, That file doesn't seem to exist. Please try again.")
                yay = 0
        """
        cred_file = open("../credentials.txt")
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
        print(self.name()+" has been started")

    def stop(self):
        print(self.name()+" has been stopped")
        self._running = False   #shut down client
        self._fsm._trade_thread.join()     #close trading thread
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
                
    def plot_session(self):
        x_axis = []
        for i in range(len(self._price_at_trade)):
            x_axis.append(i)
            
        trace1 = go.Scatter(
            x = x_axis,
            y = self._price_at_trade,
            name = 'crypto price',
            connectgaps = True
        )
        trace2 = go.Scatter(
            x = x_axis,
            y = self._history_of_portfolio_value,
            name = 'portfolio value',
            connectgaps = True
        )

        data = [trace1, trace2]

        fig = dict(data=data)
        py.plot(fig, filename=(self.name()+"_results"))

def main():
    key = "beb4b062b68a47620d306f07c8256ca2"
    secret = "IgMJoO0Xz8KHkP8wVduWVxen3BHgtnb2MjMU8mAop6VMh4/oD9oYhyizQS/fXrNIY+KclLOitutDymBZx8R+TQ=="
    passphrase = "12qpfghl23jq" 
    currency = "BTC-USD"
    socket = BotSocket(product=currency, key=key, secret=secret, passphrase=passphrase)

    BitBot1 = Bot("BitBot_1", "BTC-USD", .3, socket)
    initial_value1 = BitBot1.cash()
    
    BitBot2 = Bot("BitBot_2", "BTC-USD", .4, socket)
    initial_value2 = BitBot2.cash()
    
    BitBot3 = Bot("BitBot_3", "BTC-USD", .5, socket)
    initial_value3 = BitBot3.cash()
    
    BitBot4 = Bot("BitBot_4", "BTC-USD", .6, socket)
    initial_value4 = BitBot4.cash()
    
    BitBot1.start()
    BitBot2.start()
    BitBot3.start()
    BitBot4.start()
    
    time.sleep(300)      #makes the bot run for 6 hours. There must be a delay.
    
    BitBot1.stop()
    BitBot2.stop()
    BitBot3.stop()
    BitBot4.stop()
    
    final_value1 = BitBot1.cash() + BitBot1.crypto() * (BitBot1.historical_prices()[-1])
    cash_gain1 = round(final_value1 - initial_value1, 2)
    percent_gain1 = round((final_value1 - initial_value1) * 100 / initial_value1, 2)
    print("BitBot1 made $" + str(cash_gain1) + " (" + str(percent_gain1) + "%)")
    BitBot1.plot_session()
    
    final_value2 = BitBot2.cash() + BitBot2.crypto() * (BitBot2.historical_prices()[-1])
    cash_gain2 = round(final_value2 - initial_value2, 2)
    percent_gain2 = round((final_value2 - initial_value2) * 100 / initial_value2, 2)
    print("BitBot2 made $" + str(cash_gain2) + " (" + str(percent_gain2) + "%)")
    BitBot2.plot_session()
    
    final_value3 = BitBot3.cash() + BitBot3.crypto() * (BitBot3.historical_prices()[-1])
    cash_gain3 = round(final_value3 - initial_value3, 2)
    percent_gain3 = round((final_value3 - initial_value3) * 100 / initial_value3, 2)
    print("BitBot3 made $" + str(cash_gain3) + " (" + str(percent_gain3) + "%)")
    BitBot3.plot_session()
    
    final_value4 = BitBot4.cash() + BitBot4.crypto() * (BitBot4.historical_prices()[-1])
    cash_gain4 = round(final_value4 - initial_value4, 2)
    percent_gain4 = round((final_value4 - initial_value4) * 100 / initial_value4, 2)
    print("BitBot4 made $" + str(cash_gain4) + " (" + str(percent_gain4) + "%)")
    BitBot4.plot_session()
    
    print("Bitcoin gained " + str(round((BitBot1.historical_prices()[0] - BitBot1.historical_prices()[-1])*100/BitBot1.historical_prices()[0],2)) + "%")
    
    


main()
