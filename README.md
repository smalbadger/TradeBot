# TradeBot
Welcome to the TradeBot Repository! 

#### TODO:
+ subscribe to websocket to get real-time information
++ maintain a price history list from websocket
+ nail down the state transition algorithm
+ finish fake-trade functionality
++ plot our fake trades to see if our algorithm works or needs to be improved
+++ create functionality to make real trades
+ lots and lots of data analysis
++ use machine learning type stuff to predict behavior from order book and optimize transaction percentage amounts and state transition buffers.

+ figure out how to use tkinter - we'll use this to make the GUI unless someone has a better idea
+ figure out how to put a plotly diagram in the GUI


## Git Standards for this Repository
Please refer to [this guide](rogerdudler.github.io/git-guide/ "Git - No Deep Shit") to learn how to git gud.

For this repository, we will be following some git rules.
+ Each collaborator will create their own branch and work strictly in their branch. (mostly because I don't understand git and I'm paranoid)
+ Pay attention to what you push. This repository deals with sensitive information potentially, so don't push your API keys.

#### Simple Git cheat sheet... use this.
+ create branch - git checkout -b <new_branch>
+ pull          - git pull origin <your_branch>
+ add           - git add .
+ commit        - git commit -m "<your_commit_message>"
+ push          - git push origin <your_branch>

## Privacy policy
If you have access to this repository, please do not give access to anyone else without unanimous consent from all contributors.
The reason being that we have no idea where this is going, but it's best to keep it contained at least until we have something working.

## Credits
This project would not be possible without [danpaquin](https://github.com/danpaquin/gdax-python "danpaquin") laying the groundwork.

## Where We're going
This repository will hopefully become a collection of bots that can be pit against each other. We're hoping to collect organized data about how our bots are doing at all times and use that data to improve performance.
