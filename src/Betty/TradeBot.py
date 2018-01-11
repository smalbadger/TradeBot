from bot import *

def single_bot_run():

    socket = BotSocket(product=["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"], channels=["matches"])
    BitBot = Bot("BitBot", "LTC-USD", socket)
    
    run_time = int(input("How many minutes would you like to run the bot for?    "))
    
    BitBot.start()
    time.sleep(60*run_time)
    BitBot.stop()

single_bot_run()
