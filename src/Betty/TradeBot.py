from bot import *

def single_bot_run():
    passphrase= ""
    key=        ""
    secret=     ""

    #initialize a websocket that watches all currencies
    currency = ["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"]
    socket = BotSocket(product=currency, key=key, secret=secret, passphrase=passphrase, channels=["matches"])
    BitBot = Bot("BitBot", "LTC-USD", .3, socket)
    
    run_time = int(input("How many minutes would you like to run the bot for?    "))
    
    '''
    BitBot.start(calibration=True)
    time.sleep(60*calibration_time)
    BitBot.stop()
    
    print("\n\nCalibrating Finite State Machine\n\n")
    BitBot._fsm.calibrate(BitBot)
    print("\n\nFinished Calibrating Finite State Machine\n\n")
    '''
    
    BitBot.start()
    time.sleep(60*run_time)
    BitBot.stop()


def main():
    single_bot_run()

    
main()
