import sys
import gdax
import time
from threading import Thread

class TradeHands():
    def __init__(self, robot):
        self._robot = robot
        self._wait_time = 1
        self._running = False
        self._long_position  = None
        self._short_position = None
        
    def start(self):
        self._running = True
        
        def _trade_routine():
            while robot._running and self._running:
                # dump positions
                # aquire positions
                # Make sure to add a field called "msg_type" with a value of "trade"
                time.sleep(self._wait_time)
                
                
        self._trade_thread = Thread(target=_trade_routine)
        self._trade_thread.start()
