from datetime import datetime, timedelta

class TradingSimulation:
	def __init__(self, predictions, prices, times):
		self._num_points = len(predictions)
		self._preds  = predictions
		self._prices = prices
		self._times  = times
		self._activation_barrier = 1
		self._buy_delay = timedelta(hours = 12)
		self._dollars = 1000
		self._crypto = 0
		self._state = "wait"	# wait to sell - we need to buy first
		
	def reset(self):
		self._activation_barrier = 1
		self._buy_delay = timedelta(hours = 12)
		self._dollars = 1000
		self._crypto = 0
		self._state = "wait"	# wait to sell - we need to buy first
		
	
	def play(self):
		print("Now running simulations")
		sellTime = self._times[0]
		sellPrice = self._prices[0]
		lowPrice = sellPrice
		for i in range(self._num_points):
			if self._state == "hold":
				curPred = self._preds[i]
				if curPred >= self._activation_barrier:
					sellTime = self._times[i]
					sellPrice = self._prices[i]
					lowPrice = sellPrice
					self._state = "wait"
					self._dollars = (self._crypto * self._prices[i])# * (1-.003)
					print("SELL (w/fee): ${:7.2f} {:.6f}".format(self._dollars, self._crypto))
					self._crypto = 0
					
			elif self._state == "wait":
				curTime = self._times[i]
				
				if self._prices[i] <= (sellPrice * .997):
					if self._prices[i] <= lowPrice:
						lowPrice = self._prices[i]
					else:
						self._state = "hold"
						buyPrice = self._prices[i]
						self._crypto = (self._dollars/buyPrice)# * (1 - 0.003)
						print("BUY  (w/fee): ${:7.2f} {:.6f}".format(self._dollars, self._crypto))
						self._dollars = 0
				
				'''
				elif self._times[i] - sellTime >= self._buy_delay and self._prices[i] > sellPrice:
					self._state = "hold"
					buyPrice = self._prices[i]
					self._crypto = (self._dollars/buyPrice) * (1 - 0.003)
					print("BUY  (w/fee): ${:7.2f} {:.6f}".format(self._dollars, self._crypto))
					self._dollars = 0
				'''
				
					
		if self._dollars == 0:
			self._dollars = (self._crypto * self._prices[-1])
		print("Final portfolio value: {:.2f}".format(self._dollars))
	
