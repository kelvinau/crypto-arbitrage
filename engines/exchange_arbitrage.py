import time
from time import strftime
import grequests
from exchanges.loader import EngineLoader

class CryptoEngineExArbitrage(object):
    def __init__(self, exParams, mock=False):
        self.exParams = exParams
        self.mock = mock
        self.minProfit = 0.00005 # This may not be accurate as coins have different value        
        self.hasOpenOrder = True # always assume there are open orders first
        self.openOrderCheckCount = 0

        self.engineA = EngineLoader.getEngine(self.exParams['exchangeA']['exchange'], self.exParams['exchangeA']['keyFile'])
        self.engineB = EngineLoader.getEngine(self.exParams['exchangeB']['exchange'], self.exParams['exchangeB']['keyFile'])

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
        print self.exParams['exchangeA']['exchange']
        for order in self.engineA.openOrders:
            print order
            rs.append(self.engineA.cancel_order(order['orderId']))

        print self.exParams['exchangeB']['exchange']
        for order in self.engineB.openOrders:
            print order
            rs.append(self.engineB.cancel_order(order['orderId']))

        responses = self.send_request(rs)
        
        self.engineA.openOrders = []
        self.engineB.openOrders = []
        self.hasOpenOrder = False
        

    #Check and set current balance
    def check_balance(self):
        rs = [self.engineA.get_balance([self.exParams['exchangeA']['tickerA'], self.exParams['exchangeA']['tickerB']]),
              self.engineB.get_balance([self.exParams['exchangeB']['tickerA'], self.exParams['exchangeB']['tickerB']])]

        responses = self.send_request(rs)

        self.engineA.balance = responses[0].parsed
        self.engineB.balance = responses[1].parsed
        
        if not self.mock:
            for res in responses:
                for ticker in res.parsed:
                    # This may not be accurate
                    if res.parsed[ticker] < 0.05:
                        print ticker, res.parsed[ticker], '- Not Enough'
                        return False
        return True
    
    def rebalance(self):
        print 'rebalancing...'

    def check_orderBook(self):
        rs = [self.engineA.get_ticker_orderBook_innermost(self.exParams['exchangeA']['tickerPair']),
              self.engineB.get_ticker_orderBook_innermost(self.exParams['exchangeB']['tickerPair'])]

        responses = self.send_request(rs)
        
        print "{0} - {1}; {2} - {3}".format(
            self.exParams['exchangeA']['exchange'],
            responses[0].parsed,
            self.exParams['exchangeB']['exchange'],
            responses[1].parsed
            )

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
                    self.exParams['exchangeA']['exchange'], 
                    responses[0].parsed['ask']['price'],
                    self.exParams['exchangeB']['exchange'], 
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
                    self.exParams['exchangeB']['exchange'], 
                    responses[1].parsed['ask']['price'], 
                    self.exParams['exchangeA']['exchange'], 
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
            maxOwnAmountA = self.engineA.balance[self.exParams['exchangeA']['tickerA']] / ((1 + self.engineA.feeRatio) * askOrder['price'])
            maxOwnAmountB = self.engineB.balance[self.exParams['exchangeB']['tickerB']]
            amount = min(maxOwnAmountA, maxOwnAmountB, askOrder['amount'], bidOrder['amount'])
        # Buy from Exchange B, Sell to Exchange A
        elif type == 2:
            maxOwnAmountA = self.engineA.balance[self.exParams['exchangeA']['tickerB']]
            maxOwnAmountB = self.engineB.balance[self.exParams['exchangeB']['tickerA']] / ((1 + self.engineB.feeRatio) * askOrder['price'])
            amount = min(maxOwnAmountA, maxOwnAmountB, askOrder['amount'], bidOrder['amount'])

        return amount

    def place_order(self, status, ask, bid, amount):
        print 'placing order...'
        # Buy from Exchange A, Sell to Exchange B                
        if status == 1:
            print strftime('%Y%m%d%H%M%S') + ' Buy at {0} @ {1} & Sell at {2} @ {3} for {4}'.format(ask, self.exParams['exchangeA']['exchange'], bid, self.exParams['exchangeB']['exchange'], amount)
            rs = [
                self.engineA.place_order(self.exParams['exchangeA']['tickerPair'], 'bid', amount, ask),
                self.engineB.place_order(self.exParams['exchangeB']['tickerPair'], 'ask', amount, bid),                
            ]
        # Buy from Exchange B, Sell to Exchange A
        elif status == 2:
            print strftime('%Y%m%d%H%M%S') + ' Buy at {0} @ {1} & Sell at {2} @ {3} for {4}'.format(ask, self.exParams['exchangeB']['exchange'], bid, self.exParams['exchangeA']['exchange'], amount)
            rs = [
                self.engineB.place_order(self.exParams['exchangeB']['tickerPair'], 'bid', amount, ask),
                self.engineA.place_order(self.exParams['exchangeA']['tickerPair'], 'ask', amount, bid),                
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
    exParams = {
        'exchangeA': {
            'exchange': 'bittrex',
            'keyFile': '../keys/bittrex.key',
            'tickerPair': 'BTC-ETH',
            'tickerA': 'BTC',
            'tickerB': 'ETH'        
        },
        'exchangeB': {
            'exchange': 'bitstamp',
            'keyFile': '../keys/bitstamp.key',
            'tickerPair': 'ethbtc',
            'tickerA': 'btc',
            'tickerB': 'eth'         
        }
    }
    engine = CryptoEngineExArbitrage(exParams, True)
    #engine = CryptoEngineExArbitrage(exParams)
    engine.run()
