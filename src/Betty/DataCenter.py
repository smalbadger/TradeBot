import datetime
from datetime import datetime, timedelta

class DataCenter():
    def __init__(self, robot):
        self._robot = robot
        self._crypto_history = {"BTC-USD": [], "BCH-USD": [], "LTC-USD": [], "ETH-USD": []}
        self._trade_history  = []
        self._portfolio_history = []
        self._ma_collection = {1:[], 5:[], 10:[], 30:[], 120: []}
        #self._time_date_regex = re.compile('\dT\d.\d\w') # ^[0-9]*T[0-9]*\.[0-9]*[^0-9]*?

    def dispatch_message(self, msg):
        msg_type = msg["msg_type"]
        if msg_type == "price_match":
            self.update_crypto_history(msg)
            #self.update_moving_averages()

        elif msg_type == "trade":
            self.update_trade_history(msg)
            
        elif msg_type == "portfolio":
            self.update_portfolio_history(msg)

    def update_trade_history(self, msg):
        #each entry will take the following form:
        #   {"entry_time": None, "exit_time": None, "entry_price": None, "exit_price": None, "high_price": None, "product_id": None}
        
        self._trade_history.append(msg)

    def update_portfolio_history(self, msg):
        if msg["total"] != 0:
            self._portfolio_history.append(msg)
        
    def update_crypto_history(self, msg):
        #each entry will take the following form:
        #   {"price": None, "side": None, "time": None, "sequence": None}
        #   NOTE: other information may be available in the message. These messages come from the botsocket

        product_id        =   str(msg['product_id'])
        msg['price']      = float(msg['price'     ])
        msg['side']       =   str(msg['side'      ])
        msg['sequence']   =   int(msg['sequence'  ])
        msg['time']       = self.to_datetime(msg['time'])
        
        del msg['product_id']

        #find appropriate spot for message in price history and insert it.
        i = 0
        length = len(self._crypto_history[product_id])
        while length != 0 and msg['sequence'] < self._crypto_history[product_id][length-i-1]["sequence"]:
            i = i + 1
        if i == 0:
            self._crypto_history[product_id].append(msg)
        else:
            self._crypto_history[product_id].insert(length-i, msg)

    def update_moving_averages(self):
        #NOTE: these averages are not calculated correctly. We'll fix this later, but whatever.
    
        #each entry will take the following form:
        #   {"time": None, "simple": None, "weighted": None}
        
        currency = self._robot.currency()
        if len(self._crypto_history[currency]) == 0:
            return
        
        for average_size in self._ma_collection.keys():
            last_time = self._crypto_history[currency][-1]["time"]
            current_time_delta = timedelta(minutes=average_size)
            earliest_time = last_time - current_time_delta
            
            if self._crypto_history[currency][0]["time"] > earliest_time:
                continue
            
            index = -1
            weighted_summation = 0
            count = 0
            while self._crypto_history[currency][index]["time"] > earliest_time:
                weighted_summation += self._crypto_history[currency][index]["price"]
                count+=1
                index -= 1
                
            new_weighted_average = weighted_summation / count
            
            msg = {"time": last_time, "simple": new_weighted_average, "weighted": new_weighted_average}
            
            self._ma_collection[average_size].append(msg) 
        
                    
    def to_datetime(self, time):
        # get a datetime object from the string and append that to the message
        new_date_str = time[0:-1]
        new_date_str = new_date_str[:10] + " " + new_date_str[11:-7]
        return datetime.strptime(new_date_str, '%Y-%m-%d %H:%M:%S')

    def get_portfolio(self):
        #amount is how much of a currency you own. The value is the worth in USD
        portfolio = {"BTC-USD" : {"amount": 1, "value": 1}, 
                     "LTC-USD" : {"amount": 1, "value": 1}, 
                     "BCH-USD" : {"amount": 1, "value": 1},
                     "ETH-USD" : {"amount": 1, "value": 1}, 
                     "USD"     : {"amount": 1, "value": 1},
                     "total"   : 0,
                     "time"    : datetime.now(),
                     "msg_type": "portfolio"}
        
        need_to_return = 0
        for currency in self._crypto_history.keys():
            portfolio[currency]["amount"] = 1
            portfolio[currency]["value"]  = 1
            if len(self._crypto_history[currency]) == 0:
                need_to_return = 1

        if need_to_return:        
            return portfolio
        
        accounts = self._robot.client().get_accounts()
        
        for account in accounts:
            currency = account["currency"]
            amount = float(account["balance"])
            if currency == "BTC":
                portfolio["BTC-USD"]["amount"] = amount
                portfolio["BTC-USD"]["value"]  = amount * self._crypto_history["BTC-USD"][-1]["price"] 
                
            if currency == "BCH":
                portfolio["BCH-USD"]["amount"] = amount
                portfolio["BCH-USD"]["value"]  = amount * self._crypto_history["BCH-USD"][-1]["price"] 
            
            if currency == "ETH":
                portfolio["ETH-USD"]["amount"] = amount
                portfolio["ETH-USD"]["value"]  = amount * self._crypto_history["ETH-USD"][-1]["price"] 
            
            if currency == "LTC":
                portfolio["LTC-USD"]["amount"] = amount
                portfolio["LTC-USD"]["value"]  = amount * self._crypto_history["LTC-USD"][-1]["price"] 
            
            if currency == "USD":
                portfolio["USD"]["amount"] = amount
                portfolio["USD"]["value"]  = amount 
        
        #calculate total value:
        portfolio_keys = portfolio.keys()
        for key in portfolio_keys:
            if "USD" in key:
                portfolio["total"] += portfolio[key]["value"]
        
        return portfolio

