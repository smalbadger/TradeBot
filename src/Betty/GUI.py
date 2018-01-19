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

    ###################################################################################################
    #   function:       setup_backend
    #   purpose:        initialize the bot architecture.
    #
    #   description:    This method should only be called in the constructor for this class unless
    #                   The backend is purposefully destroyed. It will completely re-create the backend
    ###################################################################################################
    def setup_backend(self):
        socket = BotSocket(product=["BTC-USD", "LTC-USD", "ETH-USD", "BCH-USD"], channels=["matches"])
        self._bot = Bot("Betty", "LTC-USD", socket)
    
    
    
    ###################################################################################################
    #   function:       setup_frontend
    #   purpose:        Creates the GUI for the user.
    #
    #   description:    This method should only be called in the constructor for this class with no
    #                   exceptions. The GUI consists of:
    #                       start/stop buttons
    #                       portfolio pie chart
    #                       price line chart + checkboxes and radio buttons to show the moving averages
    #                       refresh button for pie chart and line chart
    #                       radio buttons to choose which currency to trade.
    ###################################################################################################
    def setup_frontend(self):
    
        ####################
        # MAIN-WINDOW SETUP
        ####################
        self._root = Tk()
        self._root.title("Betty the trade bot")
        
        #create a top and bottom frame to divide the window into 2 parts. You won't see this division in
        #the window, but it helps us lay things out properly.
        self._topframe = Frame(self._root)
        self._bottomframe = Frame(self._root)
        self._topframe.pack(side=TOP)
        self._bottomframe.pack(side=BOTTOM)
        
        self._pie_chart_frame = Frame(self._topframe)
        self._line_chart_frame = Frame(self._bottomframe)
        self._upper_dash_board = Frame(self._topframe)
        self._lower_dash_board = Frame(self._bottomframe)
        self._pie_chart_frame.pack(side=RIGHT)
        self._line_chart_frame.pack(side=RIGHT)
        self._upper_dash_board.pack(side=LEFT)
        self._lower_dash_board.pack(side=LEFT)
        
        #######################
        # WIDGET SETUP
        #######################
        #create start/stop buttons
        self._startButton = Button(self._upper_dash_board, text="Start Bot", bg="green", fg="black", command=self._bot.start)
        self._stopButton  = Button(self._upper_dash_board, text="Stop Bot" , bg="red"  , fg="white", command=self._bot.stop )
        self._startButton.grid(row=0, column=0)
        self._stopButton.grid( row=0, column=1)


            ##########################################
            # Choose currency to trade (radio buttons)
            ##########################################
        v = tk.StringVar()
        v.set("BTC-USD")

        myList = [("BTC-USD"), ("BCH-USD"), ("LTC-USD"), ("ETH-USD")]
        
        tk.Radiobutton(self._upper_dash_board, text=myList[0], padx = 20, variable=v, value=myList[0], command= lambda: self._bot.set_currency(myList[0])).grid(row=1, column=0)
        tk.Radiobutton(self._upper_dash_board, text=myList[1], padx = 20, variable=v, value=myList[1], command= lambda: self._bot.set_currency(myList[1])).grid(row=2, column=0)
        tk.Radiobutton(self._upper_dash_board, text=myList[2], padx = 20, variable=v, value=myList[2], command= lambda: self._bot.set_currency(myList[2])).grid(row=3, column=0)
        tk.Radiobutton(self._upper_dash_board, text=myList[3], padx = 20, variable=v, value=myList[3], command= lambda: self._bot.set_currency(myList[3])).grid(row=4, column=0)

            ######################################################
            # Choose which averages to show on graph (check boxes)
            ######################################################
        average_type = StringVar()
        average_type.set("simple")
        
        #This should be handled more gracefully eventually.
        CheckVars = [IntVar(), IntVar(), IntVar(), IntVar(), IntVar()] 
        myList2 = [(" SMA 120", 120), (" SMA 30", 30), (" SMA 10", 10), ("  SMA 5", 5), ("  SMA 1", 1)]
        i=0;
        
        #these widgets are to show either weighted or unweighted averages
        average_type_label = tk.Label(self._lower_dash_board, text="Average type:")
        simple_average_button   = tk.Radiobutton(self._lower_dash_board, text="simple"  , variable=average_type, value="simple"  , command= lambda: self.update_line_charts(CheckVars, myList2, average_type))
        weighted_average_button = tk.Radiobutton(self._lower_dash_board, text="weighted", variable=average_type, value="weighted", command= lambda: self.update_line_charts(CheckVars, myList2, average_type))
        average_type_label.pack()
        simple_average_button.pack()
        weighted_average_button.pack()
        
        #these widgets are check boxes for the indivicual average sizes.
        for string, size in myList2:
            x = tk.Checkbutton(self._lower_dash_board, text = string, variable = CheckVars[i], onvalue = 1, offvalue = 0, height=1, width = 6, command= lambda:self.update_line_charts(CheckVars, myList2, average_type))
            x.pack(side=BOTTOM)
            i+=1
            
            ########################################################
            # Set up the price chart and portfolio/trading chart
            ########################################################
        crypto_history = self._bot._data_center._crypto_history
        
        self._line_chart_figure = Figure(figsize=(20, 3))  
        
        self._price_plot = self._line_chart_figure.add_subplot(111)    
        self._price_plot.set_xlabel("Time")
        self._price_plot.set_ylabel("Dollars")
        self._price_plot.set_title("Price vs. Time")
        
        self._portfolio_chart_figure = Figure(figsize=(20,3))
        
        self._portfolio_plot = self._portfolio_chart_figure.add_subplot(111)        
        self._portfolio_plot.set_xlabel("Time")
        self._portfolio_plot.set_ylabel("Dollars")
        self._portfolio_plot.set_title("Portfolio Value vs. Time")

        #I don't really know how this stuff works exactly, but the purpose is to embed the plot in our window
        canvas3 = FigureCanvasTkAgg(self._portfolio_chart_figure, master=self._line_chart_frame)
        canvas3.show()
        canvas3.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        toolbar3 = NavigationToolbar2TkAgg(canvas3, self._line_chart_frame)
        toolbar3.update()
        canvas3._tkcanvas.pack(side=BOTTOM, fill=BOTH, expand=1)

        #I don't really know how this stuff works exactly, but the purpose is to embed the plot in our window
        canvas = FigureCanvasTkAgg(self._line_chart_figure, master=self._line_chart_frame)
        canvas.show()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        toolbar = NavigationToolbar2TkAgg(canvas, self._line_chart_frame)
        toolbar.update()
        canvas._tkcanvas.pack(side=BOTTOM, fill=BOTH, expand=1)
        
            ########################################################
            # Set up the pie chart 
            ########################################################
        portfolio = self._bot._data_center.get_portfolio()
        
        portfolio_keys = portfolio.keys()
        labels = [key for key in portfolio_keys if "USD" in key]
        amounts = [portfolio[key]["value"] for key in portfolio_keys if "USD" in key]
        colors = ["gold", "green", "blue", "red", "purple"]
        explode = [0,0,0,0,0]
        
        self._pie_chart_figure = Figure(figsize=(5, 3.5), dpi=100)     #we keep the pie chart figure
            
        self._pie_plot = self._pie_chart_figure.add_subplot(111)    #we also keep the sub plot
        
        self._pie_plot.pie(amounts, explode=explode, labels=labels, colors=colors, autopct='%5.2f%%', shadow=True, startangle=140)[0]   #plot the pie chart
        self._pie_chart_figure.gca().add_artist(matplotlib.patches.Circle((0,0),0.75,color='black', fc='white',linewidth=1.25))         #plot a circle over it to make a donut
        self._pie_plot.axis('equal')
        
        #I don't really know how this stuff works exactly, but the purpose is to embed the plot in our window
        canvas2 = FigureCanvasTkAgg(self._pie_chart_figure, master=self._pie_chart_frame)
        canvas2.show()
        canvas2.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        toolbar2 = NavigationToolbar2TkAgg(canvas2, self._pie_chart_frame)
        toolbar2.update()
        canvas2._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
        
        #This is the refresh button. pressing this will reset the graph and pie chart, but you still have to click the chart for it to update.
        self._refresh_button = Button(self._upper_dash_board, text="refresh graphics", bg="blue", fg="white", command= lambda: self.refresh_graphics(CheckVars, myList2, average_type))
        self._refresh_button.grid(row=0, column=2)
        
    ###################################################################################################
    #   function:       refresh_graphics
    #   purpose:        refresh both the line graph and the pie chart 
    #
    #   description:    This method is called when the refresh button is clicked, and also should be 
    #                   called automatically by another thread causing the plots to update periodically
    ###################################################################################################
    def refresh_graphics(self, CheckVars, Average_list, average_type):
        self.update_line_charts(CheckVars, Average_list, average_type)
        self.update_pie_chart()
    
    ###################################################################################################
    #   function:       update_line_chart
    #   purpose:        shows new data that was not shown the last time the chart was updated, and 
    #                   reacts to the average checkboxes being selected/deselected. 
    #
    #   description:    This will replot the entire graph, taking into account user preferences of 
    #                   averages they wish to see.
    ###################################################################################################
    def update_line_charts(self, CheckVars, Average_list, average_type):
        ###stuff dealing with the price plot
        self._price_plot.clear()
        self._portfolio_plot.clear()
        
        ma_collection       = self._bot._data_center._ma_collection
        crypto_history      = self._bot._data_center._crypto_history
        portfolio_history   = self._bot._data_center._portfolio_history
        trade_history       = self._bot._data_center._trade_history
        
        for i in range(len(CheckVars)):
            if CheckVars[i].get() == 1:
                times  = [i["time"] for i in ma_collection[Average_list[i][1]]]
                values = [i[average_type.get()] for i in ma_collection[Average_list[i][1]]]
                self._price_plot.plot_date(times, values)[0]
            else:
                self._price_plot.plot_date([],[])
        
        times  = [i["time"] for i in crypto_history[self._bot.currency()]]
        prices = [i["price"] for i in crypto_history[self._bot.currency()]]
        
        self._prices_line = self._price_plot.plot_date(times, prices)[0]
        self._line_chart_figure.autofmt_xdate()
        
        ###stuff dealing with the portfolio plot
        portfolio_history = self._bot._data_center._portfolio_history
        portfolio_values  = [element["total"] for element in portfolio_history if element["total"]!=0]
        times             = [element["time" ] for element in portfolio_history if element["total"]!=0]
        
        self._portfolio_plot.clear()
        self._portfolio_line = self._portfolio_plot.plot_date(times, portfolio_values)
        self._portfolio_chart_figure.autofmt_xdate()
        
        trade_history = self._bot._data_center._trade_history
        for trade in trade_history:
            self._portfolio_plot.axvline(x=trade["entry_time"], color="g")
            self._portfolio_plot.axvline(x=trade["exit_time"], color="r")
        
        current_position = self._bot._trading_hands._long_position
        if current_position != None:
            self._portfolio_plot.axvline(x=current_position["entry_time"], color="g")
        
    ###################################################################################################
    #   function:       update_pie_chart
    #   purpose:        re-plots the portfolio pie-chart 
    #
    #   description:    re-plots the pie-chart by first clearing all data and then plotting again.
    ###################################################################################################
    def update_pie_chart(self):
        #----------------------------Setup up pie chart ----------------------------
        portfolio = self._bot._data_center._portfolio_history[-1]
        
        portfolio_keys = portfolio.keys()
        labels = [key for key in portfolio_keys if "USD" in key]
        amounts = [portfolio[key]["value"] for key in portfolio_keys if "USD" in key]
        colors = ["gold", "green", "blue", "red", "purple"]
        explode = [0,0,0,0,0]
        
        self._pie_plot.clear()
        self._pie_plot.pie(amounts, explode=explode, labels=labels, colors=colors, autopct='%5.2f%%', shadow=True, startangle=140)[0]
        self._pie_chart_figure.gca().add_artist(matplotlib.patches.Circle((0,0),0.75,color='black', fc='white',linewidth=1.25))
        self._pie_plot.axis('equal')


def main():
    GUI = BotGUI()

main()
