import matplotlib
matplotlib.use('TkAgg')
from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from tkinter import *
from bot import *
import tkinter as tk

class BotGUI():
    def __init__(self):
        self.setup_backend()
        self.setup_frontend()
        self._root.mainloop()

    def setup_backend(self):
        socket = BotSocket(product=["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"], channels=["matches"])
        self._bot = Bot("Betty", "LTC-USD", socket)

    def setup_frontend(self):
        self._root = Tk()
        self._root.title("Betty the trade bot")

        self._topframe = Frame(self._root)
        self._topframe.pack(side=TOP)

        self._bottomframe = Frame(self._root)
        self._bottomframe.pack(side=BOTTOM)

        self._startButton = Button(self._topframe, text="Start Bot", bg="green", fg="black", command=self._bot.start)
        self._stopButton  = Button(self._topframe, text="Stop Bot", bg="red", fg="white", command=self._bot.stop)

        self._startButton.pack(side=LEFT)
        self._stopButton.pack(side=LEFT)


        # ---------------Choose which currency to trade---------------------
        v = tk.StringVar()
        v.set("BTC-USD")

        myList = [
        ("BTC-USD"),
        ("BCH-USD"),
        ("LTC-USD"),
        ("ETH-USD"),
        ]
        
        tk.Radiobutton(self._root, text=myList[0], padx = 20, variable=v, value=myList[0], command= lambda: self._bot.set_currency(myList[0])).pack(anchor=tk.W)
        tk.Radiobutton(self._root, text=myList[1], padx = 20, variable=v, value=myList[1], command= lambda: self._bot.set_currency(myList[1])).pack(anchor=tk.W)
        tk.Radiobutton(self._root, text=myList[2], padx = 20, variable=v, value=myList[2], command= lambda: self._bot.set_currency(myList[2])).pack(anchor=tk.W)
        tk.Radiobutton(self._root, text=myList[3], padx = 20, variable=v, value=myList[3], command= lambda: self._bot.set_currency(myList[3])).pack(anchor=tk.W)
        # ---------------Choose which currency to trade---------------------



        # ---------------Choose which lines to display on graph---------------------
        
        average_type = StringVar()
        average_type.set("simple")
        
        
        # the check values should be 1 if on and 0 if off.
        CheckVars = [IntVar(), IntVar(), IntVar(), IntVar(), IntVar()]
        '''
        CheckVar1 = IntVar()
        CheckVar2 = IntVar()
        CheckVar3 = IntVar()
        CheckVar4 = IntVar()
        CheckVar5 = IntVar()
        '''
        myList2 = [
        (" SMA 120", 120), # CheckVar[4]
        (" SMA 30", 30),  # CheckVar[3]
        (" SMA 10", 10),  # CheckVar[2]
        ("  SMA 5", 5),  # CheckVar[1]
        ("  SMA 1", 1),  # CheckVar[0]
        ]
        i=0;
        
        average_type_label = tk.Label(self._root, text="Average type:")
        simple_average_button   = tk.Radiobutton(self._root, text="simple"  , variable=average_type, value="simple"  , command= lambda: self.update_line_chart(CheckVars, myList2, average_type))
        weighted_average_button = tk.Radiobutton(self._root, text="weighted", variable=average_type, value="weighted", command= lambda: self.update_line_chart(CheckVars, myList2, average_type))
        average_type_label.pack()
        simple_average_button.pack()
        weighted_average_button.pack()
        
        for string, size in myList2:
            x = tk.Checkbutton(text = string, variable = CheckVars[i], onvalue = 1, offvalue = 0, height=1, width = 6, command= lambda:self.update_line_chart(CheckVars, myList2, average_type))
            x.pack(side=BOTTOM)
            i+=1
        # ---------------Choose which lines to display on graph---------------------
        
        
        #----------------------------Setup up line graph----------------------------
        crypto_history = self._bot._data_center._crypto_history
        
        self._figure = Figure(figsize=(5, 4), dpi=100)
        self._sub_plot = self._figure.add_subplot(111)
        self._sub_plot.set_xlabel("Time")
        self._sub_plot.set_ylabel("Dollars")
        self._sub_plot.set_title("Value vs. Time")
        
        times  = [i["time"] for i in crypto_history[self._bot.currency()]]
        prices = [i["price"] for i in crypto_history[self._bot.currency()]]
        self._prices_line = self._sub_plot.plot_date(times, prices)[0]
        
        canvas = FigureCanvasTkAgg(self._figure, master=self._root)
        canvas.show()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        toolbar = NavigationToolbar2TkAgg(canvas, self._root)
        toolbar.update()
        canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
        
        self._figure.autofmt_xdate()
        #----------------------------Setup up line graph----------------------------
    
    def update_line_chart(self, CheckVars, Average_list, average_type):
        self._sub_plot.clear()
        
        ma_collection       = self._bot._data_center._ma_collection
        crypto_history      = self._bot._data_center._crypto_history
        portfolio_history   = self._bot._data_center._portfolio_history
        trade_history       = self._bot._data_center._trade_history
        
        print("-----------------")
        print("showing averages:")
        for i in range(len(CheckVars)):
            if CheckVars[i].get() == 1:
                times  = [i["time"] for i in ma_collection[Average_list[i][1]]]
                values = [i[average_type.get()] for i in ma_collection[Average_list[i][1]]]
                self._sub_plot.plot_date(times, values)[0]
                print(Average_list[i][1])
            else:
                self._sub_plot.plot_date([],[])
        print("-----------------")
        
        times  = [i["time"] for i in crypto_history[self._bot.currency()]]
        prices = [i["price"] for i in crypto_history[self._bot.currency()]]
        
        self._prices_line = self._sub_plot.plot_date(times, prices)[0]
        self._figure.autofmt_xdate()
        
        #self._prices_line.set_data(times, prices)
        #self._figure.canvas.draw()
        
        """
        This code should go in the function that created the pie chart...
        
        portfolio = self._bot._data_center.get_portfolio()
        total_val = portfolio["USD"]["value"]+portfolio["BTC-USD"]["value"]+portfolio["ETH-USD"]["value"]+portfolio["BCH-USD"]["value"]+portfolio["LTC-USD"]["value"]
        BTC_percent = portfolio["BTC-USD"]["value"]/total_val
        LTC_percent = portfolio["LTC-USD"]["value"]/total_val
        ETH_percent = portfolio["ETH-USD"]["value"]/total_val
        BCH_percent = portfolio["BCH-USD"]["value"]/total_val
        USD_percent = portfolio["USD"]["value"]/total_val
        """
        



def main():
    GUI = BotGUI()

main()
