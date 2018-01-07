"""
    Author: Sam Badger
    
    This file contains both the state and finite state machine classes. They are grouped together because
    they are really depend on each other. The finite state machine contains 6 states:
    
        "Critical-Sell" - Emergency state to dump all. This is a failsafe that hopefully will never be visited.
        "Strong-Sell"   - sell a specific amount of holdings every specific amount of time
        "Weak-Sell"     - sell a specific amount of holdings every specific amount of time
        "Hold"          - We don't know what to do at this point, so we won't do anything.
        "Weak-Buy"      - buy a specific amount of holdings every specific amount of time
        "Strong-Buy"    - buy a specific amount of holdings every specific amount of time
    
    The finite state machine starts at the "Hold" state. If the price increases by a certain percent, we move toward the buy states.
    If the price decreases by a certain amount, we move toward the sell states. The Hold state does not trade at all, the weak states
    trade a certain percent of the available balance, and the strong states trade more. The critical sell state will trade the most.
"""

import sys
import gdax
import time
from threading import Thread

################################################################################
#                                 STATE                                        #
################################################################################
class state():
    def __init__(self, state_id, name, next=None, prev=None, transaction_percent=0, next_buffer=0, prev_buffer=0):
        self._id = state_id
        self._name = name
        self._transaction_percent = transaction_percent
        self._next = next
        self._prev = prev
        self._next_buffer = next_buffer
        self._prev_buffer = prev_buffer
        self._low = 10000000
        self._high = 0
        self._entry = 0
        self._transaction_type = None

        if "Sell" in name:
            self._transaction_type = "sell"
        elif "Buy" in name:
            self._transaction_type = "buy"
        elif "Hold" in name:
            self._transaction_type = "hold"
    
    #####################
    ##---- GETTERS ----##
    #####################
    def next(self):
        return self._next
        
    def prev(self):
        return self._prev
            
    def next_buffer(self):
        return self._next_buffer
        
    def prev_buffer(self):
        return self._prev_buffer
        
    def transaction_percent(self):
        return self._transaction_percent
        
    def name(self):
        return self._name
        
    def entry(self):
        return self._entry
        
    def thresholds(self):
        return {"high": self._high, "low": self._low}
        
    def transaction_type(self):
        return self._transaction_type
        
    def id(self):
        return self._id
        
        
    #####################
    ##---- SETTERS ----##
    #####################
    def set_next_buffer(self, new_buffer):
        self._next_buffer = new_buffer

    def set_prev_buffer(self, new_buffer):
        self._prev_buffer = new_buffer

    def set_high(self, new_high):
        self._high = new_high
		
    def set_low(self, new_low):
        self._low = new_low
		
    def set_transaction_percent(self, new_percent):
        self._transaction_percent = new_percent
        
        
    #####################
    ##--Miscellaneous--##
    #####################
    def trade(self, bot, fake=True, portfolio=None, prices=None, historical_prices=None):
        if historical_prices == None:
            historical_prices = bot.historical_prices()
            
        if len(historical_prices)==0:
            return
            
        side = self.transaction_type()
        
        order_result = "None"
        
        price = historical_prices[-1]['price']
        time = historical_prices[-1]["time"]
        if fake == True:
            available_cash = bot.cash()
            available_crypto = bot.crypto()
            
            if side == "buy":
                #print("currently buying {}%".format(self.transaction_percent()))
                
                transaction_cash_value = available_cash * self.transaction_percent() / 100
                fees = transaction_cash_value * .003 #assume that we'll always get charged the .3% buy fee.
                transaction_crypto_size = transaction_cash_value / price
                
                bot._cash = bot.cash() - transaction_cash_value# - fees
                bot._crypto = bot.crypto() + transaction_crypto_size
                
                order_result = bot.client().buy(size=str(transaction_crypto_size), product_id=bot.currency(), type="market")
                
            elif side == "sell":
                #print("currently selling {}%".format(self.transaction_percent()))
                transaction_crypto_size = available_crypto * self.transaction_percent() / 100
                transaction_cash_value = price * transaction_crypto_size
                
                bot._cash = bot.cash() + transaction_cash_value
                bot._crypto = bot.crypto() - transaction_crypto_size
                
                order_result = bot.client().sell(size=str(transaction_crypto_size), product_id=bot.currency(), type="market")
                
            #print("Available cash: " + str(bot.cash()))
            
            prices.append({"value": price, "time": time})
            portfolio.append({"value": bot.cash() + bot.crypto() * price, "state": self.id()-1, "time": time})
            
        else:
            available_cash, available_crypto = bot.get_balances()
                        
            if side == "buy":
                #print("currently buying {}%".format(self.transaction_percent()))
                
                transaction_cash_value = available_cash * self.transaction_percent() / 100
                fees = transaction_cash_value * .003 #assume that we'll always get charged the .3% buy fee.
                transaction_crypto_size = round(transaction_cash_value / price,6)
                
                order_result = bot.client().buy(size=str(transaction_crypto_size), product_id=bot.currency(), type="market")
                
            elif side == "sell":
                #print("currently selling {}%".format(self.transaction_percent()))
                transaction_crypto_size = round(available_crypto * self.transaction_percent() / 100, 6)
                transaction_cash_value = price * transaction_crypto_size
                
                order_result = bot.client().sell(size=str(transaction_crypto_size), product_id=bot.currency(), type="market")
                
            #print("Available cash: " + str(bot.cash()))
            
            prices.append({"value": price, "time": time})
            portfolio.append({"value": available_cash + available_crypto * price, "state": self.id()-1, "time": time})
            
            fills=0
            for page in bot.client().get_fills():
                for fill in page:
                    fills+=1
            if "message" in order_result:
                print("attempted {} -> {}".format(side, order_result["message"]))
            print("orders: {}".format(bot.client().get_orders()))
            print("fills:  {}".format(fills))
################################################################################
#                           FINITE STATE MACHINE                               #
################################################################################
class FSM():
    def __init__(self, state_log_file_name="state_log.txt", trade_delay=5, state_usage=[1,2,3,4,5,6]):
        #The state usage field might be slightly confusing. Basically, you just specify which states you want to be active.
        #Probably most common will be [1,2,3,4,5,6] or [3,4,5]. If you choose to not use all the states, you must
        #specify adjacent states. Something like [1,3,4,6] is not allowed.
        #note that all 6 states will still be created, but we will limit access to only the states listed.
        CS = state(1, "Critical-Sell", transaction_percent=80, next_buffer=.1  , prev_buffer=None) #state 1
        SS = state(2,   "Strong-Sell", transaction_percent=60, next_buffer=.1  , prev_buffer=5   ) #state 2
        WS = state(3,     "Weak-Sell", transaction_percent=40, next_buffer=.1  , prev_buffer=.3  ) #state 3
        H  = state(4,          "Hold", transaction_percent=0 , next_buffer=.1  , prev_buffer=.3  ) #state 4
        WB = state(5,      "Weak-Buy", transaction_percent=40, next_buffer=.1  , prev_buffer=.3  ) #state 5
        SB = state(6,    "Strong-Buy", transaction_percent=60, next_buffer=None, prev_buffer=.3  ) #state 6

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

        self._current_state = H
        self._trade_thread = None
        self._state_log_file_name = state_log_file_name
        self._state_log = open(state_log_file_name, "w")
        self._trade_delay = trade_delay
        self._state_usage = state_usage
        
        self.print_states()
        
    #####################
    ##---- GETTERS ----##
    #####################
    def current_state(self):
        return self._current_state
        
    def state_log(self):
        return self._state_log
        
    def state_log_file_name(self):
        return self._state_log_file_name
        
    def trade_thread(self):
        return self._trade_thread
        
    def trade_delay(self):
        return self._trade_delay

    def state_usage(self):
        return self._state_usage
        
    #####################
    ##--Miscellaneous--##
    #####################
    def print_states(self):
        state = self.current_state()
        while state.prev() != None:
            state = state.prev()
            
        print("FSM states:")
        while state != None:
            msg = "name: {:20}   transaction percent: {:.2f}".format(state.name(), state.transaction_percent())
            if state.next_buffer() != None:
                msg = msg + "   next buffer: {:.2f}".format(state.next_buffer())
            if state.prev_buffer() != None:
                msg = msg + "   prev buffer: {:.2f}".format(state.prev_buffer())
                
            print(msg)
            state = state.next()
    
    def change_state(self, history, should_print_to_log=True, should_print_to_stdout=False):
        #This method should be given an up-to-date history of prices - preferably coming from the websocket.
        
        moving_average_len = 1
        
        if len(history) < moving_average_len:
            return
            
        moving_average = 0
        for i in range(moving_average_len):
            i = (i+1) * (-1)
            moving_average = moving_average + history[i]["price"]
            
        moving_average = moving_average/moving_average_len

        last_price = history[-1]['price']
        
        if last_price == 0: #this should obviously never be zero, but let's avoid a division by zero error.
            return

        cur_state = self.current_state()
        thresh = cur_state.thresholds()
        high = thresh["high"]
        low = thresh["low"]
        entry = cur_state.entry()
        
        if entry == 0:  #the first state (hold) may not have an entry price, so we just set it.
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
            if moving_average < (high - high * cur_state.prev_buffer()/100):
                next_state = cur_state.prev()

        elif cur_state.name() == "Weak-Buy":
            if moving_average < (high - high * cur_state.prev_buffer()/100):
                next_state = cur_state.prev()
            #if moving_average < (entry - entry * (cur_state.prev_buffer()/100)):
            #    next_state = cur_state.prev()
            elif moving_average > (entry + entry * cur_state.next_buffer()/100):
                next_state = cur_state.next()
        
        elif cur_state.name() == "Hold":
            if moving_average < (entry - entry * (cur_state.prev_buffer()/100)):
                next_state = cur_state.prev()
            elif moving_average > (entry + entry * cur_state.next_buffer()/100):
                next_state = cur_state.next()
        
        elif cur_state.name() == "Weak-Sell":
            if moving_average < (entry - entry * (cur_state.prev_buffer()/100)):
                next_state = cur_state.prev()
            #elif moving_average > (entry + entry * cur_state.next_buffer()/100):
            #    next_state = cur_state.next()
            elif moving_average > (low + low * cur_state.next_buffer()/100):
                next_state = cur_state.next()

        elif cur_state.name() == "Strong-Sell":
            if moving_average < (entry - entry * cur_state.prev_buffer()/100):
                next_state = cur_state.prev()
            elif moving_average > (low + low * cur_state.next_buffer()/100):
                next_state = cur_state.next()

        elif cur_state.name() == "Critical-Sell":
            if moving_average > (low + low * cur_state.next_buffer()/100):
                next_state = cur_state.next()

        else:
            print("ERROR: bot is at unknown state. Please check the logs." + "  ->  " + cur_state.name())
            sys.exit(1)
        
        if next_state.id() in self.state_usage():
            percent_change = ((last_price - cur_state.entry())/cur_state.entry())*100
            message = "{} -> {}\tentry price: {:.2f}\tpercent change:{:.3f}%".format(cur_state.name(), next_state.name(), cur_state.entry(), percent_change)
            
            if should_print_to_log:
                self._state_log.write(message+"\n")
            if should_print_to_stdout:
                print(message)
                
            if next_state != cur_state:
                next_state._entry = last_price
                
            self._current_state = next_state
            
    def update_fsm_values(self, weak_percent, strong_percent, critical_percent, prev_buffer, next_buffer):
        state = self.current_state()
        while state.prev() != None:
            state = state.prev()
            
        while state != None:
            if state.prev_buffer() != None:
                state._prev_buffer = prev_buffer
            if state.next_buffer() != None:
                state._next_buffer = next_buffer
            if "Weak" in state.name():
                state._transaction_percent = weak_percent
            elif "Strong" in state.name():
                state._transaction_percent = strong_percent
            elif "Critical" in state.name():
                state._transaction_percent = critical_percent
            state = state.next()
    
    def calibrate(self, robot):
        #this method should be called after the bot has performed fake trades. It will go through a range of values and try to find the best combination.
        portfolio = self._calibration_portfolio_list
        prices = self._calibration_prices_list 
        calibration_file = open("calibration_file.txt", "w")
        best_portfolio = 0
        print("history length for calibration: {}".format(len(robot.historical_prices())))
        for weak_percent in [5, 15]:
            for strong_percent in [25, 50]:
                for critical_percent in [60, 90]:
                    for prev_buffer in [.2, .9]:
                        for next_buffer in [.2, .9]:
                            # redo trade routine
                            calib_portfolio = []
                            calib_prices = []
                            
                            self.update_fsm_values(weak_percent, strong_percent, critical_percent, prev_buffer, next_buffer)
                            
                            for i in prices:
                                self.change_state([{"price": i["value"]}])
                                self.current_state().trade(robot, fake=True, portfolio=calib_portfolio, prices=calib_prices, historical_prices=[{"price": i["value"], "time": i["time"]}])
                            
                            if calib_portfolio[-1]["value"] > best_portfolio:
                                best_porfolio = calib_portfolio[-1]["value"]
                                best_configuration = {"weak": weak_percent, "strong": strong_percent, "critical": critical_percent, "prev_buffer": prev_buffer, "next_buffer": next_buffer}
                                calibration_file.write("best configuration: {}   ->  {}\n".format(best_configuration, best_portfolio))
                                print("best configuration: {}   ->  {}\n".format(best_configuration, best_portfolio))
                                
        self.update_fsm_values(best_configuration["weak"], best_configuration["strong"], best_configuration["critical"], best_configuration["prev_buffer"], best_configuration["next_buffer"])
                                                           
    def run(self, robot, calibration=False):
        def _trade_routine():
            if calibration:
                self._calibration_portfolio_list = []
                self._calibration_prices_list = []
                portfolio = self._calibration_portfolio_list
                prices = self._calibration_prices_list
            else:
                robot._portfolio_at_trading = []
                robot._prices_at_trading = []
                portfolio = robot._portfolio_at_trading
                prices = robot._prices_at_trading
                
            while robot._running:
                self.change_state(robot.historical_prices())
                self.current_state().trade(robot, fake=True, portfolio=portfolio, prices=prices)
                time.sleep(self.trade_delay())
                
            

        self._trade_thread = Thread(target=_trade_routine)
        self._trade_thread.start()
