# Welcome to the Bot Library!
This document lists all of our bots and their current status. If you're a developer, please make sure to update the status of the bots that you work on.

Bots are listed in alphabetic order, which happens to be the order that they were created. 

Our best girl: *Angela*

### Angela
| Category           | Bot-Specific explanation                                                                          |
| ------------------:|:------------------------------------------------------------------------------------------------- |
| Profit Status      | Not profitable                                                                                    |
| Development Status | Abandoned for having a bad trading algorithm                                                      |
| Trading Method     | Uses a finite state machine to move across the buy/sell spectrum                                  |
| Intended Market    | Large price swings with no static                                                                 |
| Pitfall            | Static. Even with strong trends, static causes this bot to be unprofitable


### Betty
| Category           | Bot-Specific explanation                                                                           |
| ------------------:|:-------------------------------------------------------------------------------------------------- |
| Profit Status      | Not profitable                                                                                     |
| Development Status | Under development                                                                                  |
| Trading Method     | Uses moving average crossings to initiate buy/short-sell and trailing stops to initiate sell/cover |
| Intended Market    | large price swings                                                                                 |
| Pitfall            | Misleading market momentum                                                                         |
