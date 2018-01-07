from bot import *

def four_bot_competition():
    key=None
    secret=None
    passphrase=None

    currency = "BTC-USD"
    socket = BotSocket(product=currency, key=key, secret=secret, passphrase=passphrase)

    BitBot1 = Bot("BitBot_1", "BTC-USD", .3, socket)
    initial_value1 = BitBot1.cash()
    
    BitBot2 = Bot("BitBot_2", "BTC-USD", .4, socket)
    initial_value2 = BitBot2.cash()
    
    BitBot3 = Bot("BitBot_3", "BTC-USD", .5, socket)
    initial_value3 = BitBot3.cash()
    
    BitBot4 = Bot("BitBot_4", "BTC-USD", .6, socket)
    initial_value4 = BitBot4.cash()
    
    BitBot1.start()
    BitBot2.start()
    BitBot3.start()
    BitBot4.start()
    
    time.sleep(300)      #makes the bot run for 6 hours. There must be a delay.
    
    BitBot1.stop()
    BitBot2.stop()
    BitBot3.stop()
    BitBot4.stop()
    
    final_value1 = BitBot1.cash() + BitBot1.crypto() * (BitBot1.historical_prices()[-1])
    cash_gain1 = round(final_value1 - initial_value1, 2)
    percent_gain1 = round((final_value1 - initial_value1) * 100 / initial_value1, 2)
    print("BitBot1 made $" + str(cash_gain1) + " (" + str(percent_gain1) + "%)")
    BitBot1.plot_session()
    
    final_value2 = BitBot2.cash() + BitBot2.crypto() * (BitBot2.historical_prices()[-1])
    cash_gain2 = round(final_value2 - initial_value2, 2)
    percent_gain2 = round((final_value2 - initial_value2) * 100 / initial_value2, 2)
    print("BitBot2 made $" + str(cash_gain2) + " (" + str(percent_gain2) + "%)")
    BitBot2.plot_session()
    
    final_value3 = BitBot3.cash() + BitBot3.crypto() * (BitBot3.historical_prices()[-1])
    cash_gain3 = round(final_value3 - initial_value3, 2)
    percent_gain3 = round((final_value3 - initial_value3) * 100 / initial_value3, 2)
    print("BitBot3 made $" + str(cash_gain3) + " (" + str(percent_gain3) + "%)")
    BitBot3.plot_session()
    
    final_value4 = BitBot4.cash() + BitBot4.crypto() * (BitBot4.historical_prices()[-1])
    cash_gain4 = round(final_value4 - initial_value4, 2)
    percent_gain4 = round((final_value4 - initial_value4) * 100 / initial_value4, 2)
    print("BitBot4 made $" + str(cash_gain4) + " (" + str(percent_gain4) + "%)")
    BitBot4.plot_session()
    
    print("Bitcoin gained " + str(round((BitBot1.historical_prices()[0] - BitBot1.historical_prices()[-1])*100/BitBot1.historical_prices()[0],2)) + "%")

def single_bot_run():
    passphrase= ""
    key=        ""
    secret=     ""

    #initialize a websocket that watches all currencies
    currency = ["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"]
    socket = BotSocket(product=currency, key=key, secret=secret, passphrase=passphrase, channels=["matches"])
    BitBot = Bot("BitBot", "LTC-USD", .3, socket)
    
    #calibration_time = int(input("How many minutes would you like to calibrate the bot for?    "))
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
