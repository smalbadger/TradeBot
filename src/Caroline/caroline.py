from bot import *
from time import sleep

socket = BotSocket(product=["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"], channels=["matches"])
bot = Bot("Caroline", "LTC-USD", socket)
bot.start()
