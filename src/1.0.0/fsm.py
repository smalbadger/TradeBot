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

import gdax
import sys
import time
from threading import Thread

################################################################################
#                                 STATE                                        #
################################################################################
class state():
    def __init__(self, state_id, name, next=None, prev=None, transaction_percent=0, next_buffer=None, prev_buffer=None):
        self._id = state_id
        self._name = name
        self._transaction_percent = 0
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
    def trade(self, bot, fake=True):
        side = self.transaction_type()
        
        if side is "hold":
            return
            
            
        if fake is True:
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
    def __init__(self, state_log_file_name="state_log.txt", trade_delay=0.5, state_usage=[1,2,3,4,5,6]):
        #The state usage field might be slightly confusing. Basically, you just specify which states you want to be active.
        #Probably most common will be [1,2,3,4,5,6] or [3,4,5]. If you choose to not use all the states, you must
        #specify adjacent states. Something like [1,3,4,6] is not allowed.
        #note that all 6 states will still be created, but we will limit access to only the states listed.
        CS = state(1, "Critical-Sell", transaction_percent=50, next_buffer=3)                  #state 1
        SS = state(2, "  Strong-Sell", transaction_percent=20, next_buffer=.4, prev_buffer=10) #state 2
        WS = state(3, "    Weak-Sell", transaction_percent=10, next_buffer=.4, prev_buffer=.4) #state 3
        H  = state(4, "         Hold", transaction_percent=0 , next_buffer=.4, prev_buffer=.4) #state 4
        WB = state(5, "     Weak-Buy", transaction_precent=10, next_buffer=.4, prev_buffer=.4) #state 5
        SB = state(6, "   Strong-Buy", transaction_percent=20, prev_buffer=.4)                 #state 6

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
    def change_state(self, history, should_print_to_log=True, should_print_to_stdout=False):
        #This method should be given an up-to-date history of prices - preferably coming from the websocket.
        
        if len(history) == 0:
            return

        last_price = history[-1]
        
        if last_price == 0: #this should obviously never be zero, but let's avoid an error.
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
            if last_price < (high - high * cur_state.prev_buffer()/100):
                next_state = cur_state.prev()

        elif cur_state.name() == "Weak-Buy":
            if last_price < (entry - entry * (cur_state.prev_buffer()/100)):
                next_state = cur_state.prev()
            elif last_price > (entry + entry * cur_state.next_buffer()/100):
                next_state = cur_state.next()
        
        elif cur_state.name() == "Hold":
            if last_price < (entry - entry * (cur_state.prev_buffer()/100)):
                next_state = cur_state.prev()
            elif last_price > (entry + entry * cur_state.next_buffer()/100):
                next_state = cur_state.next()
        
        elif cur_state.name() == "Weak-Sell":
            if last_price < (entry - entry * (cur_state.prev_buffer()/100)):
                next_state = cur_state.prev()
            elif last_price > (entry + entry * cur_state.next_buffer()/100):
                next_state = cur_state.next()

        elif cur_state.name() == "Strong-Sell":
            if last_price < (low + low * cur_state.prev_buffer()/100):  #only move to critical sell if the price decreases 10% after reaching strong sell state
                next_state = cur_state.prev()
            elif last_price > (low + low * cur_state.next_buffer()/100):
                next_state = cur_state.next()

        elif cur_state.name() == "Critical-Sell":
            if last_price > (low + low * cur_state.next_buffer()/100):
                next_state = cur_state.next()

        else:
            print("ERROR: bot is at unknown state. Please check the logs.")
            sys.exit(1)
        
        if next_state.id() in self.state_usage():
            percent_change = (last_price - cur_state.entry())/cur_state.entry()
            message = "{} -> {}\tentry price: {:.2f}\tpercent change:{:.3f}%".format(cur_state.name(), next_state.name(), cur_state.entry(), percent_change)
            
            if should_print_to_log:
                self._state_log.write(message+"\n")
            if should_print_to_stdout:
                print(message)
                
            if next_state != cur_state:
                next_state._entry = last_price
                
            self._current_state = next_state
        
        
    def run(self, robot):
        def _trade_routine():
            while robot._running:
                self.change_state(robot.historical_prices())
                self.current_state().trade(robot)
                time.sleep(self.trade_delay())
            self._state_log.close()
            robot.create_portfolio()

        self._trade_thread = Thread(target=_trade_routine)
        self._trade_thread.start()
