import time
from rules import RuleChecker
import threading

class CryptoEngineRules:
    '''
    exchange = filename
    '''
    def __init__(self, exchange, ticker, rule, keyFile):
        self.exchange = exchange
        self.ticker = ticker
        self.rule = rule
        self.keyFile = keyFile
        self.checker = RuleChecker()
  
    
    def start_engine(self):
        print 'starting engine...'
        mod = __import__(self.exchange)
        cls = mod.ExchangeEngine()
        cls.load_key(self.keyFile)

        while True:
            ''' For history of about 1 hour ago to now '''
            data = cls.get_ticker_history(self.ticker)
            parsedData = cls.parseTickerData(self.ticker, data)
            self.checker.check(self.rule, parsedData)
            time.sleep(cls.sleepTime)
    
    def run(self):
        thread = threading.Thread(target=self.start_engine)
        #thread.daemon = True # thread is terminated when the main script terminates
        thread.start()

if __name__ == '__main__':
    exchange = 'gatecoin'
    ticker = 'BTCHKD'
    rule = 'oldest_latest_avg_of_5_larger_than_5per'
    keyFile = '../.keys/gatecoinkey'
    engine = CryptoEngineRules(exchange, ticker, rule, keyFile)
    engine.run()
    
    exchange = 'kraken'
    ticker = 'XRPUSD'
    rule = 'oldest_latest_avg_of_5_larger_than_5per'
    keyFile = '../.keys/krakenkey'
    engine = CryptoEngineRules(exchange, ticker, rule, keyFile)
    engine.run()