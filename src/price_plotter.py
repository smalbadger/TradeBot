import gdax

def main():
    Client = gdax.PublicClient()
    history = Client.get_product_historic_rates("BTC-USD", granularity=30)

    #history is a list of lists. Each of the inner lists has the time, high, low, open, close, and volume of each candle. Note that the time is in "linux epoch" format meaning it is the number of seconds since january 1st 1970.

    #I'm just printing each of the lists here.
    for item in history:
        print(item)

    #now I'll make a list of only the times...
    times = []
    for item in history:
        times.append(item[0])

    #now I'll make a list of only the price averages...
    averages = []
    for item in history:
        av = (item[1] + item[2])/2
        averages.append(av)

    for i in range(0, len(times)):
        print(str(times[i]) + ": " + str(averages[i]))

    #task:
    #use the 2 lists above (times and averages) and make a nice lil plot using plotly.
    #NOTE: Before using plotly, you'll have to install their libraries. just go to your command line and type "pip install plotly" (without the quotes of course)
main()
