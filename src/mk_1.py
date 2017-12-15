import gdax


### global credential variables read from file
### WARNING! If you are hard coding these variables, DO NOT push to git
passphrase = "qg4ptkd4m2bj"
key = "6b88670423d87e9393498ad7ac540a82"
secret = "YHSxlOLfA+KViY/UDsJY9FQiYbHGO//D3SOn7GFFpXatHNMU82pJQoKhAsJRoITfBNI0AWQHwImmD1HhjZBs2w=="
###
###


class state():
    """
        This class contains information for a single state of the finite state machine.
    """
    def __init__(self, name, next, prev):
        self._name = name
        self._transaction_percent = 5
        self._next = next
        self._prev = prev

    def next(self):
        return self._next

    def prev(self):
        return self._prev

    def percent(self):
        return self._transaction_percent

    def name(self):
        return self._name

    def update_percent(self, new_percent):
        self._transaction_percent = new_percent

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
"""
class FSM():
    def __init__(self, product):
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
        self._currency = product
        self._historic_prices = list()

    def current_state(self):
        return self._current_state

    def currency(self):
        return self._currency

    def historic_prices(self):
        return self._historic_prices

    def update_historic_prices(self, new):
        #This will change. I don't actually want to update the whole list,
        #I just want to put new values at the front of it and take values off the end
        #so that we don't use too much memory.
        self._historic_prices = new

def print_prices(client):
    for i in client.get_products():
        p_id = i["id"]
        if "USD" in p_id:
            print(p_id + " : " + str(client.get_product_ticker(product_id=p_id)["price"]))

def main():
    client = gdax.AuthenticatedClient(key, secret, passphrase)
    btc_fsm = FSM("BTC")
    print_prices(client)

main()
