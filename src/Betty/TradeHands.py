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
        self._paper_trading = False
        self._sell_cushion = .5
        self._trade_duration = "medium"
        
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
                
                if self._trade_duration == "short":
                    sma_a = sma_1
                    sma_b = sma_5
                elif self._trade_duration == "medium":
                    sma_a = sma_5
                    sma_b = sma_10
                elif sefl._trade_duration == "long":
                    sma_a = sma_10
                    sma_b = sma_30
                else:
                    print("Unkown Trade Duration")
                    
                self._enough_info_to_trade = len(sma_a) >= 2 and len(sma_b) >= 2
                
                if not self._enough_info_to_trade:
                    continue
                
                sma_a_1 = sma_a[-2]
                sma_a_2 = sma_a[-1]
                sma_b_1 = sma_b[-2]
                sma_b_2 = sma_b[-1]
                last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
                
                if self._long_position != None and last_price > self._long_position["high_price"]:
                    self._long_position["high_price"] = last_price
                
                #sell if the price decreases from the highest point by a certain percent, or if teh sma1 crosses the sma5 goin downward.
                if self._long_position != None:
                    if last_price <= (self._long_position["high_price"] * (1-self._sell_cushion/100)):
                        self.sell()
                        #add our position to the trade history
                        DC.dispatch_message(deepcopy(self._long_position))
                        self._long_position = None
                            
                #buy if the sma10 crosses the sma30 going upward.
                if self._long_position == None:
                    if sma_a_1["simple"] <= sma_b_1["simple"] and sma_a_2["simple"] >= sma_b_2["simple"]:
                        #record our position
                        self._long_position = {"entry_time": None, "exit_time": None, "entry_price": 0, "exit_price": None, "high_price": 0, "msg_type": "trade"}
                        self.buy()    

        self._trade_thread = Thread(target=_trade_routine)
        self._trade_thread.start()
        
    def buy(self):
        print("\t\t\t\t\t\t\t\t\t\tBUYING")
        bot = self._robot
        DC = bot._data_center
        last_price = last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
        self._long_position["entry_price"] = last_price
        self._long_position["high_price"]  = last_price
        self._long_position["entry_time"]  = datetime.now()
        
        if self._paper_trading:
            crypto_trade_amount = bot._fake_cash / last_price
            bot._fake_crypto += crypto_trade_amount
            bot._fake_cash -= crypto_trade_amount * last_price
            
        else:
            available_cash = DC._portfolio_history[-1]["USD"]["amount"]
            target_price = round(last_price*1.001, 2)
            transaction_crypto_size = round(available_cash / (target_price),6)
            while transaction_crypto_size * target_price > available_cash:
                transaction_crypto_size -= .01
            order_msg = bot.client().buy(size=str(transaction_crypto_size), product_id=bot.currency(), price=str(target_price), type="limit", post_only=True)
            
            if "message" in order_msg:
                print(order_msg["message"])
                print("Attempted to buy {:5.2f} {} @ ${:5.2f} for a total of ${:5.2f}".format(transaction_cryto_size, bot.currency(), target_price, transaction_crypto_size*target_price))
            else:
                print(msg)
            
    def sell(self):
        print("\t\t\t\t\t\t\t\t\t\tSELLING")
        bot = self._robot
        DC = bot._data_center
        last_price = last_price = DC._crypto_history[self._robot.currency()][-1]["price"]
        if self._long_position != None:
            self._long_position["exit_price"] = last_price
            self._long_position["exit_time"]  = datetime.now()
            
        if self._paper_trading:
            cash_trade_amount = bot._fake_crypto * last_price
            bot._fake_cash += cash_trade_amount
            bot._fake_crypto -= cash_trade_amount / last_price
            
        else:
            available_currency = DC._portfolio_history[-1][bot.currency()]["amount"]
            target_price = round(last_price*0.999, 2)
            order_msg = bot.client().sell(size=str(available_currency), product_id=bot.currency(), price=str(target_price), type="limit", post_only=True)
            print(order_msg)
            
    def set_sell_cushion(self, new_cushion):
        self._sell_cushion = float(new_cushion)
        
    def set_trade_duration(self, duration):
        print("new duration: " + duration)
        self._trade_duration = duration
        
    def get_trade_duration(self):
        return self._trade_duration
