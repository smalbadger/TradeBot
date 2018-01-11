
# Hi, my name is Angela
### - the worst trading bot known to man kind! 
This document will walk you through my architecture

##### (Angela is not profitable yet, and she probably never will be. She's kinda self concious about it though.)
Disclaimer: This bot's code is not commented very well and reading it will result in immediate heightened levels of stress. This bot also acts as a proof of concept and a prototype. It most likely contains bugs, and you should not run it unless you wish to loss money.

## Bot
<pre>                            
           /\                   This is the Bot object. It is the highest level of looking at the trading program, The user will      
           \/               only interact with this class through a GUI. Each Bot will only be able to trade a single cryptocurrency,
           ||               so the user will be able to start/stop each bot. Right now, GDAX only supports Bitcoin, Bitcoin Cash, Ethereum,
          _||_              and Litecoin, so only 4 bots can run at a time. Let's go over the components of the Bot:
         /    \        
________/______\________        + Passphrase, Secret, Key - These are credentials that should be stored in a file to be read by the program.
|                      |          The default directory to place it is the TradBot folder, but it can be stored anywhere.
|                      |
|    _____    _____    |        + Client - This is the AuthenticatedClient object that is used to interact with your GDAX account. It uses 
|    |   |    |   |    |          the credentials above to log into your account. This is what allows the bot to see account balances, place
|    |   |    |   |    |          orders, and do other misellaneous things on behalf of you. 
|    -----    -----    |
|                      |        + BotSocket - This is what gives us constant information about product prices, volume, trades being placed and
|                      |          other related things. Once we subscribe, we get constant information and place it into the appropriate history list
|      ___________     |
|     /_|_|_|_|_|_\    |        + FSM - This is the finite state machine that we're using to trade. It contains six State objects. Each Object has a
|                      |          trade associated with it, and we always decide if we want to change states, then trade, then wait for a set
------------------------          amount of time and repeat. 
        |       |                                         
                                + Name - The name of the Bot can be anything you want it to be. Each Bot should have a different name as a unique identifier.
                                  
                                + currency - Each Bot can only trade one cryptocurrency, so this is the field that keeps track of the currency that the bot 
                                  can trade. The field should be a string such as "BTC-USD", "BCH-USD", "LTC-USD", or "ETH-USD".
                                  
    It is important to note that each Bot requires its own thread to run on. This is to ensure the fastest possible trading. To determine if you have enough 
threads to run another Bot, you need to see how many threads your processor has. To do this, try finding system information, or system preferences on your 
computer, and google your exact processor model. You should see the number of cores and threads on your processor. To find how many bots you can spawn do 
the following calculation: Bots = (cores * threads) - 1
                   
We are subtracting one because the BotSocket also requires its own thread. Because of this, we should have all the Bot instantiations share a single websocket.
</pre>

## BotSocket
<pre>
_________________________       This is the BotSocket object. If you couldn't tell, the picture is a solid object going into a 
|                       |   space. Don't judge, I'm no Artist. The BotSocket class is really just a wrapper of the WebSocket
|                       |   class. I just add on a few of my own variables and store data however I want. Any history that is
|       __________      |   kept will member variables of this class. There are many member variables of the WebSocket, so you
|      /  _    _  \     |   you can look at those yourself, but the fields added into the BotSocket class are listed below:
|     /  | |  | |  \    |
|    |   | |  | |   |   |       + history_size - We can only keep a certain amount of history before we run out of memory. 
|    |   | |  | |   |   |         I don't know that this has to be used, but it should be. 
|     \  |_|  |_|  /    |                                  
|      \__________/     |       + history - We keep the history of all cryptocurrencies in a dictionary. Each key is the product_id 
|                       |         such as "BTC-USD". The value of each key is a list of dictionaries where each element of the list
|           ()          |         has the fields "price", "side", "time", and "sequence". Note that you can store any other information
|       __________      |         by adding to the "on_message" method.
|      /  _    _  \     |                                  
|     /  | |  | |  \    |       + message_count - Every time we recieve a message, we add one to this field. This field is useless
|    |   | |  | |   |   |         for now, but feel free to use it if you want.
|    |   | |  | |   |   |
|     \  |_|  |_|  /    |
|      \__________/     |
|                       |
|                       |
|_______________________|
</pre>                                 
                                  
## Finite State Machine
<pre>
    /----\                      Although the FSM (Finite State Machine) and State classes are separate from each other, we'll
    | CS |                  describe them together since they are practically inseparable. Basically, this is what decides if
    \----/                  we need to buy or sell and if so, how much. Here's how the trading algorithm works:
     ^  |
     |  |                       1. Gather some data about the currency. See the BotSocket section to see the information that
     |  v                          we're keeping for this version.
    /----\
    | SS |                      2. Look at the currency history and decide if we're in the correct state or if we should change. 
    \----/
     ^  |                       3. Execute the trade associated with the current state.
     |  |
     |  v                       4. wait for a set amount of time.
    /----\
    | WS |                      Now that you have a basic idea of the trading algorithm, I'll give you more details about the variables
    \----/                  that are in these classes.
     ^  |
     |  |               State variables:
     |  v                       The state class holds variables that allow us to know what type of trade we're doing, what state we're at,
    /----\                  and how much to buy or sell along with the buffer that the price will have to break to change states in either
    |HOLD|                  direction. Furthermore, it contains variables that describe the high, low, and entry prices that the currency
    \----/                  has reached while being in that state. These states are linked together by holding references to the next and
     ^  |                   previous states (like a doubly linked list). Note that this is intended to make the buy/sell decision less
     |  |                   volatile. 
     |  v          
    /----\              FSM variables:
    | WB |                      The FSM class holds variables that keep track of the current state, set a minimum time between trades, 
    \----/                  and most importantly, the six states that we can move between. We can also limit the number of states by
     ^  |                   creating a list of state_ids that we want to use. the default list is [1,2,3,4,5,6] which uses all states,
     |  |                   but we could limit the state usage to [3,4,5] or any other sequence of continuous states. The FSM also 
     |  v                   keeps track of the trading thread which will have to be tied up after trading is done. 
    /----\
    | SB |
    \----/
</pre>   
    
## GDAX Client
<pre>
    /-----\                     This is the Client Object. You can read more about it on danpaquin's repository, since he wrote the code.
    |     |      /-----\    There is a link to his page in the readme file in the TradeBot directory. Although I really just wanted to 
    |   oo|      |oo   |    draw two dudes shaking hands with symbols, I guess I'll give an explanation of what the Client class does.
    |    _|      |_    |
    \_____/      \_____/        Really, the client class simply allows you to interact with GDAX from your program. There are 2 types of clients. 
       |            |       the first is the PublicClient. This is its own class and does not require that you authorize your account, or even
      /|\          /|\      that you have an account. It allows you to get basic information about product prices, price history, etc. The second 
     / | \        / | \     type of client is the AuthorizedClient. This class requires you to have an API key, passphrase, and secret, and
     \ |  \--8---/  | |     allows you to interact with your account through your application. depending on the priviledges that you give your API
      \|            | |     key, you can make trades, cancel orders, get account balances, and do anything that the PublicClient can do.
       w            | w
       /\           /\
      /  \         /  \
     /    \       /    \
</pre>























