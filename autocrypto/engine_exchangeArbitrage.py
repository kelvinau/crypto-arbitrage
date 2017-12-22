import time
from time import strftime
import grequests

class CryptoEngineArbitrage(object):
    def __init__(self, exchangeA, exchangeB, mock=False):
        self.exchangeA = exchangeA
        self.exchangeB = exchangeB
        self.mock = mock
        self.minProfit = 0.00005 # This is not accurate as coins have different value

        mod = __import__(self.exchangeA['exchange'])
        self.engineA = mod.ExchangeEngine()
        self.engineA.load_key(self.exchangeA['keyFile'])

        mod = __import__(self.exchangeB['exchange'])
        self.engineB = mod.ExchangeEngine()
        self.engineB.load_key(self.exchangeB['keyFile'])   
        
        self.hasOpenOrder = True # always assume there are open orders first
        self.openOrderCheckCount = 0

    def start_engine(self):
        print strftime('%Y%m%d%H%M%S') + ' starting Exchange Arbitrage Engine...'
        if self.mock:
            print '---------------------------- MOCK MODE ----------------------------'
        #Send the request asynchronously
        while True:
            try:
                if not self.mock and self.hasOpenOrder:
                    self.check_openOrder()
                else:
                    if self.check_balance():
                        bookStatus = self.check_orderBook()
                        if bookStatus['status']:
                            self.place_order(bookStatus['status'], bookStatus['ask'], bookStatus['bid'], bookStatus['maxAmount'])
                    else:
                        self.rebalance()
            except Exception, e:
                print e

            #time.sleep(self.engineA.sleepTime)
            time.sleep(self.engineA.sleepTime + 10)
            
    def check_openOrder(self):
        if self.openOrderCheckCount >= 5:
            self.cancel_allOrders()
        else:
            print 'checking open orders...'
            rs = [self.engineA.get_open_order(),
                  self.engineB.get_open_order()]
            responses = self.send_request(rs)

            if not responses[0] or not responses[1]:
                print responses
                return False
            
            if responses[0].parsed or responses[1].parsed:
                self.engineA.openOrders = responses[0].parsed
                self.engineB.openOrders = responses[1].parsed
                print self.engineA.openOrders, self.engineB.openOrders
                self.openOrderCheckCount += 1
            else:
                self.hasOpenOrder = False
                print 'no open orders'
                print 'starting to check order book...'
    
    def cancel_allOrders(self):
        print 'cancelling all open orders...'
        rs = []
        print self.exchangeA['exchange']
        for order in self.engineA.openOrders:
            print order
            rs.append(self.engineA.cancel_order(order['orderId']))

        print self.exchangeB['exchange']
        for order in self.engineB.openOrders:
            print order
            rs.append(self.engineB.cancel_order(order['orderId']))

        responses = self.send_request(rs)
        
        self.engineA.openOrders = []
        self.engineB.openOrders = []
        self.hasOpenOrder = False
        

    #Check and set current balance
    def check_balance(self):
        rs = [self.engineA.get_balance([self.exchangeA['tickerA'], self.exchangeA['tickerB']]),
              self.engineB.get_balance([self.exchangeB['tickerA'], self.exchangeB['tickerB']])]

        responses = self.send_request(rs)

        self.engineA.balance = responses[0].parsed
        self.engineB.balance = responses[1].parsed
        
        if not self.mock:
            for res in responses:
                for ticker in res.parsed:
                    # This is not correct
                    if res.parsed[ticker] < 0.05:
                        print ticker, res.parsed[ticker], '- Not Enough'
                        return False
        return True
    
    def rebalance(self):
        print 'rebalancing...'

    def check_orderBook(self):
        rs = [self.engineA.get_ticker_orderBook_innermost(self.exchangeA['tickerPair']),
              self.engineB.get_ticker_orderBook_innermost(self.exchangeB['tickerPair'])]

        responses = self.send_request(rs)
        
        #print responses[0].parsed, responses[1].parsed

        diff_A = responses[0].parsed['ask']['price'] - responses[1].parsed['bid']['price']
        diff_B = responses[1].parsed['ask']['price'] - responses[0].parsed['bid']['price']
        if diff_A < 0 and diff_B < 0 and abs(diff_A) < abs(diff_B):
            diff_A = 0
        # Buy from Exchange A, Sell to Exchange B
        if diff_A < 0:
            maxAmount = self.getMaxAmount(responses[0].parsed['ask'], responses[1].parsed['bid'], 1)
            fee = self.engineA.feeRatio * maxAmount * responses[0].parsed['ask']['price'] + self.engineB.feeRatio * maxAmount * responses[1].parsed['bid']['price']

            if abs(diff_A * maxAmount) - fee > self.minProfit:
                print "{0}'s Ask {1} - {2}'s Bid {3} < 0".format(
                    self.exchangeA['exchange'], 
                    responses[0].parsed['ask']['price'],
                    self.exchangeB['exchange'], 
                    responses[1].parsed['bid']['price'])       
                print '{0} (diff) * {1} (amount) = {2}, commission fee: {3}'.format(diff_A, maxAmount, abs(diff_A * maxAmount), fee)            
                return {'status': 1, 'ask': responses[0].parsed['ask']['price'], 'bid': responses[1].parsed['bid']['price'], 'maxAmount': maxAmount}
            else:
                return {'status': 0}

        # Buy from Exchange B, Sell to Exchange A
        elif diff_B < 0:
            maxAmount = self.getMaxAmount(responses[1].parsed['ask'], responses[0].parsed['bid'], 2)
            fee = self.engineB.feeRatio * maxAmount * responses[1].parsed['ask']['price'] + self.engineA.feeRatio * maxAmount * responses[0].parsed['bid']['price']

            if abs(diff_B * maxAmount) - fee > self.minProfit:
                print "{0}'s Ask {1} - {2}'s Bid {3} < 0".format(
                    self.exchangeB['exchange'], 
                    responses[1].parsed['ask']['price'], 
                    self.exchangeA['exchange'], 
                    responses[0].parsed['bid']['price'])             
                print '{0} (diff) * {1} (amount) = {2}, commission fee: {3}'.format(diff_B, maxAmount, abs(diff_B * maxAmount), fee)   
                return {'status': 2, 'ask': responses[1].parsed['ask']['price'], 'bid': responses[0].parsed['bid']['price'], 'maxAmount': maxAmount}
            else:
                return {'status': 0}

        return {'status': 0}

    def getMaxAmount(self, askOrder, bidOrder, type):
        amount = 0
        # Buy from Exchange A, Sell to Exchange B
        if type == 1:
            maxOwnAmountA = self.engineA.balance[self.exchangeA['tickerA']] / ((1 + self.engineA.feeRatio) * askOrder['price'])
            maxOwnAmountB = self.engineB.balance[self.exchangeB['tickerB']]
            amount = min(maxOwnAmountA, maxOwnAmountB, askOrder['amount'], bidOrder['amount'])
        # Buy from Exchange B, Sell to Exchange A
        elif type == 2:
            maxOwnAmountA = self.engineA.balance[self.exchangeA['tickerB']]
            maxOwnAmountB = self.engineB.balance[self.exchangeB['tickerA']] / ((1 + self.engineB.feeRatio) * askOrder['price'])
            amount = min(maxOwnAmountA, maxOwnAmountB, askOrder['amount'], bidOrder['amount'])

        return amount

    def place_order(self, status, ask, bid, amount):
        print 'placing order...'
        # Buy from Exchange A, Sell to Exchange B                
        if status == 1:
            print strftime('%Y%m%d%H%M%S') + ' Buy at {0} @ {1} & Sell at {2} @ {3} for {4}'.format(ask, self.exchangeA['exchange'], bid, self.exchangeB['exchange'], amount)
            rs = [
                self.engineA.place_order(self.exchangeA['tickerPair'], 'bid', amount, ask),
                self.engineB.place_order(self.exchangeB['tickerPair'], 'ask', amount, bid),                
            ]
        # Buy from Exchange B, Sell to Exchange A
        elif status == 2:
            print strftime('%Y%m%d%H%M%S') + ' Buy at {0} @ {1} & Sell at {2} @ {3} for {4}'.format(ask, self.exchangeB['exchange'], bid, self.exchangeA['exchange'], amount)
            rs = [
                self.engineB.place_order(self.exchangeB['tickerPair'], 'bid', amount, ask),
                self.engineA.place_order(self.exchangeA['tickerPair'], 'ask', amount, bid),                
            ]

        if not self.mock:
            responses = self.send_request(rs)
        self.hasOpenOrder = True
        self.openOrderCheckCount = 0

    def send_request(self, rs):
        responses = grequests.map(rs)
        for res in responses:
            if not res:
                print responses
                raise Exception
        return responses

    def run(self):
        self.start_engine()

if __name__ == '__main__':
    exchangeA = {
        'exchange': 'bittrex',
        'keyFile': '../.keys/bittrexkey',
        'tickerPair': 'BTC-ETH',
        'tickerA': 'BTC',
        'tickerB': 'ETH'
        }
    exchangeB = {
        'exchange': 'bitstamp',
        'keyFile': '../.keys/bitstampkey',
        'tickerPair': 'ethbtc',
        'tickerA': 'btc',
        'tickerB': 'eth' 
        }    
    engine = CryptoEngineArbitrage(exchangeA, exchangeB, True)
    #engine = CryptoEngineArbitrage(exchangeA, exchangeB)
    engine.run()
