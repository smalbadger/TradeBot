import sys
import gdax
import time
from threading import Thread

class TradeHands():
    def __init__(self, robot):
        self._robot = robot
        self._wait_time = 1
        self._running = False
        self._long_position  = {"time": None, "entry_price": 0, "exit_price": 0}
        self._acquire_position = True
        self._enough_info_to_trade = False
        self._paper_trading = True
        
    def start(self):
        self._running = True

        def _trade_routine():
        
            print("Starting Trading Hands")
            DC = self._robot._data_center
            sma_10 = DC._ma_collection[10]
            sma_30 = DC._ma_collection[30]
            trading_attempts = 0
            
            while self._robot._running and self._running:
                time.sleep(self._wait_time)
                
                print("\t\t\t\t\t\t\t\ttrading attempts -> ", trading_attempts)
                trading_attempts += 1
                did_trade = 0
                
                #record the current portfolio values.
                self._robot._data_center.dispatch_message(self._data_center.get_portfolio())
                self._robot._data_center.update_moving_averages()
                self._enough_info_to_trade = len(sma_10) >= 2 and len(sma_30) >= 2
                
                if not self._enough_info_to_trade:
                    continue
                
                sma_10_1 = sma_10[-2]
                sma_10_2 = sma_10[-1]
                sma_30_1 = sma_30[-2]
                sma_30_2 = sma_30[-1]
                last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
                
                msg = {}
                
                # dump positions
                if not self._acquire_position:
                    if self._long_position != None:
                        if last_price <= self._long_position["exit_price"]:
                            self.sell()
                            self._acquire_position = True
                            msg["side"]  = "sell"
                            did_trade = 1
                            
                # aquire positions
                if self._acquire_position and not did_trade:
                    if self._long_position == None:
                        if sma_10_1 < sma_30_1 and sma_10_2 > sma_30_2:
                            self.buy()
                            self._acquire_position = False
                            msg["side"]  = "buy"
                            did_trade = 1
                            
                if trade_flag:                
                    msg["time"]     = self._crypto_history[self._robot.currency()][-1]["time"]
                    msg["price"]    = last_price
                    msg["volume"]   = None # this should change later
                    msg["msg_type"] = ["trade"]
                    
                    print(msg)
                    
                    DC.dispatch_message(msg)
                

        self._trade_thread = Thread(target=_trade_routine)
        self._trade_thread.start()
        
    def buy(self):
        #TODO: need to account for 0.3% fee on market buy
        
        bot = self._robot
        DC = bot._data_center
        last_price = last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
        if self._paper_trading:
            self._robot._fake_crypto += bot._fake_cash / last_price
            self._robot._fake_cash -= self._robot._fake_crypto * last_price
            
        else:
            pass
            
    def sell(self):
        bot = self._robot
        DC = bot._data_center
        last_price = last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
        if self._paper_trading:
            self._robot._fake_cash += self._robot._fake_crypto * last_price
            self._robot._fake_crypto -= bot._fake_crypto / last_price
            
        else:
            pass
