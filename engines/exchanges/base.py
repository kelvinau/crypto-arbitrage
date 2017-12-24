from abc import ABCMeta, abstractmethod
import json

class ExchangeEngineBase:
    __metaclass__ = ABCMeta
    @abstractmethod
    def __init__(self):
        pass
    
    def load_key(self, filename):
        with open(filename) as f:    
            self.key = json.load(f)
            
    @abstractmethod
    def _send_request(self):
        pass
    
    @abstractmethod
    def place_order(self, ticker, action, amount, price):
        pass
  
    @abstractmethod
    def get_balance(self):
        pass
    
    
    #@abstractmethod
    def get_ticker_history(self, ticker):
        pass
    
   
       
    '''
    Format: e.g. {'exchange': 'gatecoin', 'ticker': 'BTCHKD', 'data': [{price: (int)30.5}]}
    '''
    #@abstractmethod
    def parseTickerData(self, tickerData):
        pass