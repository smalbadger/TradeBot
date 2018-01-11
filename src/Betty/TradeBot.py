from bot import *

def single_bot_run():

    socket = BotSocket(product=["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"], channels=["matches"])
    Betty = Bot("BitBot", "LTC-USD", socket)
    
    run_time = int(input("How many minutes would you like to run the bot for?    "))
    
    Betty.start()
    time.sleep(60*run_time)
    Betty.stop()

single_bot_run()
