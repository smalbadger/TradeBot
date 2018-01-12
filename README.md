# TradeBot
Welcome to the TradeBot Repository! 

### Getting started:
+ learn python - we use python3
+ get familiar with our repository
+ install the unofficial GDAX python API -> windows: pip install gdax -> unix: pip3 install gdax
+ install and configure plotly. Look up instructions on the plotly website. It's fairly straight forward.
+ watch videos on Udemy. My login credentials are in the file called "udemy_credentials.txt". Feel free to access the courses through my account and purchase any courses that you think would be relevant to this project :)
+ contribute to a bot and make sure to document it!


## Git Standards for this Repository
Please refer to [this guide](rogerdudler.github.io/git-guide/ "Git - No Deep Shit") to learn simple git.

For this repository, we will be following some git rules.
+ Each collaborator will create their own branch and work strictly in their branch. (mostly because I don't understand git and I'm paranoid)
+ Pay attention to what you push. This repository deals with sensitive information potentially, so don't push your API keys, passprhase, or secret. checkout the .git ignore file. It shows where I keep my GDAX credentials and how I format it to be read by the bots. 

#### Simple Git cheat sheet... use this.
+ create branch - git checkout -b <new_branch>
+ pull          - git pull origin <your_branch>
+ add           - git add .
+ commit        - git commit -m "<your_commit_message>"
+ push          - git push origin HEAD:<your_branch>

## Credits
This project would not be possible without [danpaquin](https://github.com/danpaquin/gdax-python "danpaquin") laying the groundwork.

## Where We're going
This repository will be a collection of bots - each one having a unique architecture and trading algorithm. If you want to contribute, I recommend copying/pasting a bot into another directory, renaming it, and make your changes. We're naming the bots alphabetically and only girls names, so if there is a bot with a C name, but not one with a D name, rename your bot Danielle or something. Of course you can start from scratch as well.
