import sys
import gdax
import time
from threading import Thread
from copy import deepcopy
from datetime import datetime

class TradeHands():
    def __init__(self, robot):
        self._robot = robot
        self._wait_time = 1
        self._running = False
        self._long_position  = None
        self._acquire_position = True
        self._enough_info_to_trade = False
        self._paper_trading = True
        
    def start(self):
        self._running = True

        def _trade_routine():
        
            print("Starting Trading Hands")
            DC = self._robot._data_center
                       
            while self._robot._running and self._running:
                time.sleep(self._wait_time)
                
                
                #record the current portfolio values.
                sma_1  = DC._ma_collection[ 1]
                sma_5  = DC._ma_collection[ 5]
                sma_10 = DC._ma_collection[10]
                sma_30 = DC._ma_collection[30]
                
                self._robot._data_center.dispatch_message(self._robot._data_center.get_portfolio())
                
                self._robot._data_center.update_moving_averages()
                
                self._enough_info_to_trade = len(sma_1) >= 2 and len(sma_5) >= 2
                
                if not self._enough_info_to_trade:
                    continue
                
                sma_1_1 = sma_1[-2]
                sma_1_2 = sma_1[-1]
                sma_5_1 = sma_5[-2]
                sma_5_2 = sma_5[-1]
                #sma_10_1 = sma_10[-2]
                #sma_10_2 = sma_10[-1]
                #sma_30_1 = sma_30[-2]
                #sma_30_2 = sma_30[-1]
                last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
                
                if self._long_position != None and last_price > self._long_position["high_price"]:
                    self._long_position["high_price"] = last_price
                
                
                
                if self._long_position != None:
                    if last_price <= (self._long_position["high_price"] * .99):
                        self.sell()
                        #add our position to the trade history
                        DC.dispatch_message(deepcopy(self._long_position))
                        self._long_position = None
                            
                if self._long_position == None:
                    if sma_1_1["weighted"] < sma_5_1["weighted"] and sma_1_2["weighted"] > sma_5_2["weighted"]:
                        #record our position
                        self._long_position = {"entry_time": None, "exit_time": None, "entry_price": 0, "exit_price": None, "high_price": 0, "msg_type": "trade"}
                        self.buy()
                
                
        self._trade_thread = Thread(target=_trade_routine)
        self._trade_thread.start()
        
    def buy(self):
        #TODO: need to account for 0.3% fee on market buy
        print("\t\t\t\t\t\t\t\t\t\tBUYING")
        bot = self._robot
        DC = bot._data_center
        last_price = last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
        self._long_position["entry_price"] = last_price
        self._long_position["high_price"]  = last_price
        self._long_position["entry_time"]  = datetime.now()
        if self._paper_trading:
            self._robot._fake_crypto += bot._fake_cash / last_price
            self._robot._fake_cash -= self._robot._fake_crypto * last_price
            
        else:
            pass
            
    def sell(self):
        print("\t\t\t\t\t\t\t\t\t\tSELLING")
        bot = self._robot
        DC = bot._data_center
        last_price = last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
        if self._long_position != None:
            self._long_position["exit_price"] = last_price
            self._long_position["exit_time"]  = datetime.now()
        if self._paper_trading:
            self._robot._fake_cash += self._robot._fake_crypto * last_price
            self._robot._fake_crypto -= bot._fake_crypto / last_price
            
        else:
            pass
