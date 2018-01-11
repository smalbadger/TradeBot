
class DataCenter():
    def __init__(self):
        self._crypto_history = {"BTC-USD": [], "BCH-USD": [], "LTC-USD": [], "ETH-USD": []}
        self._trade_history  = [{"time": None, "side": None, "volume": None, "price": None}]
        self._portfolio_at_trading = ["time": None, "value": None] 
        self._sma_collection = {
                                5:   [{"time": None, "simple": None, "weighted": None}], 
                                10:  [{"time": None, "simple": None, "weighted": None}],  
                                30:  [{"time": None, "simple": None, "weighted": None}],   
                                60:  [{"time": None, "simple": None, "weighted": None}],   
                                120: [{"time": None, "simple": None, "weighted": None}]
                               }
                               
    def dispatch_message(self, msg):
        msg_type = msg["msg_type"]
        
        if msg_type == "price_match":
            self.update_crypto_history(msg)
            self.update_MA()
            
        elif msg_type == "trade":
            self.update_trade_history()
            self.update_portfolio_history()
        
    def update_trade_history(self, msg):
        pass
        
    def update_portfolio_history(self):
        pass
        
    def update_crypto_history(self, msg):
        product_id =   str(msg['product_id'])
        price      = float(msg['price'     ])
        side       =   str(msg['side'      ])
        time       =   str(msg['time'      ])
        sequence   =   int(msg['sequence'  ])
        
        #find appropriate spot for message in price history and insert it.
        i = 0
        length = len(self._crypto_history[msg['product_id']])
        while length != 0 and msg['sequence'] < self._crypto_history[msg['product_id']][length-i-1]["sequence"]:
            i = i + 1
        if i == 0:
            self._crypto_history[msg['product_id']].append({"price": price, "side": side, "time": time, "sequence": sequence})
        else:
            self._crypto_history[msg['product_id']].insert(length-i, {"price": price, "side": side, "time": time, "sequence": sequence})
        
    def update_MA(self):
        pass
