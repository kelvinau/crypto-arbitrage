# Crypto Arbitrage
## Introduction
This is an automatic trading bot using Triangular or Exchange Arbitrages. It reguarly checks and detects arbitrage opportunities, and place orders when a profit can be made.  
Started with $1000 in October, there were some times that this made about $40/day for a few weeks with Triangular Arbitrage on Bittrex, but as the market is getting very unstable, the profit is hard to outrun the high price fluctuation.

## Exchanges
Bittrex, Bitfinex, Bitstamp, Kraken, Gatecoin

## Setup
1. `pip install grequests`
2. Add the API keys in the key file under .keys
Triangular: Modify the values of `exchange`  
Exchange: Modify the values of `exchangeA` and `exchangeB`

## Usage
Triangular: `python engine_triangularArbitrage.py`  
Exchange: `python engine_exchangeArbitrage.py`

## Difficulties
1. The trading fee is the largest obstacle. Most of the exchanges have a 0.25% fee. The profit will be larger if the fee can be lower.
2. Sometimes not all the placed orders are executed, so there will be some manual work to rebalance. The bot should be able to deal with this situation, such as placing a market order, instead of just cancelling the open orders.

## Further Improvement
1. Implement exchange rebalancing
2. Handle open orders strategically
3. Refactoring  

I will put this project on hold now as the price goes up and down so much. Hope this can help anyone with similar interests.