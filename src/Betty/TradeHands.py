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
        self._short_position = {"time": None, "entry_price": 0, "exit_price": 0}
        self._acquire_position = True
        self._paper_trading = True
        
    def start(self):
        self._running = True

        def _trade_routine():
        
            print("Starting Trading Hands")
            DC = self._robot._data_center
            sma_1 = DC._ma_collection[1]
            sma_5 = DC._ma_collection[5]
            trading_attempts = 0
            
            while self._robot._running and self._running:
                time.sleep(self._wait_time)
                print("\t\t\t\t\t\t\t\ttrading attempts -> ", trading_attempts)
                trading_attempts += 1
                trade_flag = 0
                
                self._robot._data_center.update_moving_averages()
                
                if len(sma_1) < 2 or len(sma_5) < 2:
                    continue
                
                sma_1_1 = sma_1[-2]
                sma_1_2 = sma_1[-1]
                sma_5_1 = sma_5[-2]
                sma_5_2 = sma_5[-1]
                last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
                
                msg = {}
                
                # dump positions
                if not self._acquire_position:
                    if self._long_position != None:
                        if last_price <= self._long_position["exit_price"]:
                            self.sell()
                            self._acquire_position = True
                            msg["side"]  = "sell"
                            trade_flag = 1
                            
                    if self._short_position != None:
                        if last_price >= self._short_position["exit_price"]:
                            #self.cover()
                            self._acquire_position = True
                            msg["side"]  = "short-sell"
                            trade_flag = 1
                            
                            
                # aquire positions
                if self._acquire_position:
                    if self._long_position == None:
                        if sma_1_1 < sma_5_1 and sma_1_2 > sma_5_2:
                            self.buy()
                            self._acquire_position = False
                            msg["side"]  = "buy"
                            trade_flag = 1
                            
                    if self._short_position == None:
                        if sma_1_1 > sma_5_1 and sma_1_2 < sma_5_2:
                            #self.short_sell()
                            self._acquire_position = False
                            msg["side"]  = "cover"
                            trade_flag = 1
                            
                if trade_flag:                
                    msg["time"]  = self._crypto_history[self._robot.currency()][-1]["time"]
                    msg["price"] = last_price
                    msg["volume"]= None # this should change later
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
            self._robot._fake_crypto -= bot._fake_cash / last_price
            
        else:
            pass
    
    def short_sell(self):
        bot = self._robot
        DC = bot._data_center
        last_price = last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
        if self._paper_trading:
            self._robot._fake_cash += self._robot._fake_crypto * last_price
            self._robot._fake_crypto -= bot._fake_cash / last_price
            
        else:
            pass
        
    def cover(self):
        #TODO: need to account for 0.3% fee on market buy
        bot = self._robot
        DC = bot._data_center
        last_price = last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
        if self._paper_trading:
            self._robot._fake_crypto += bot._fake_cash / last_price
            self._robot._fake_cash -= self._robot._fake_crypto * last_price
            
        else:
            pass
