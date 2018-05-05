from datetime import datetime, timedelta

class TradingSimulation:
	def __init__(self, predictions, prices, times):
		self._num_points = len(predictions)
		self._preds  = predictions
		self._prices = prices
		self._times  = times
		self._activation_barrier = 1
		self._buy_delay = timedelta(minutes = 3)
		self._dollars = 1000
		self._crypto = 0
		self._state = "wait"	# wait to sell - we need to buy first
	
	def play(self):
		print("Now running simulations")
		sellTime = self._times[0]
		for i in range(self._num_points):
			if self._state == "hold":
				curPred = self._preds[i]
				if curPred >= self._activation_barrier:
					sellTime = self._times[i]
					self._state = "wait"
					self._dollars = (self._crypto * self._prices[i]) #* (1-.003)
					print("SELL (w/fee): ${:7.2f} {:.6f}".format(self._dollars, self._crypto))
					self._crypto = 0
					
			elif self._state == "wait":
				curTime = self._times[i]
				if curTime >= sellTime + self._buy_delay:
					self._state = "hold"
					buyPrice = self._prices[i]
					self._crypto = (self._dollars/buyPrice) # * (1 - 0.003)
					print("BUY  (w/fee): ${:7.2f} {:.6f}".format(self._dollars, self._crypto))
					self._dollars = 0
	
	def play_sweep(self, min_barrier=0, max_barrier=1, barrier_step=.1):
		pass
