'''
        Maker(%)    Taker(%)    Volume (BTC)
          0.25       0.35        50 
          0.2        0.3         100
          0.15       0.25        200
          0.12       0.2         500
          0.1        0.16        1,300 
          0.08       0.14        2,600
          0.06       0.13        5,200
          0.05       0.12        13,000
          0.04       0.11        20,000
MAX       0.02       0.1
'''

from imports import *

class ExchangeEngine(ExchangeEngineBase):
    def __init__(self):
        self.API_URL = 'https://api.gatecoin.com/'
        self.sleepTime = 1
                        
    def _send_request(self, command, httpMethod, params={}):          
        now = str(time.time())
        contentType = "" if httpMethod == "GET" else "application/json"
        
        url = self.API_URL + command

        if httpMethod == "DELETE":
            R = requests.delete
        elif httpMethod == "GET":
            R = requests.get
        elif httpMethod == "POST":
            R = requests.post          
        data = json.dumps(params)

        headers = {}
        if not any(x in command for x in ['Public', 'public']):
            secret = self.key['private'].encode()
            message = (httpMethod + url + contentType + now).lower().encode()
      
            signature = hmac.new(secret, msg=message.encode(), digestmod=hashlib.sha256).digest()
            hashInBase64 = base64.b64encode(signature, altchars=None)
    
            headers = {
                'API_PUBLIC_KEY': self.key['public'],
                'API_REQUEST_SIGNATURE': hashInBase64,
                'API_REQUEST_DATE': now,
                'Content-Type': 'application/json'
            }            
            
        response = R(url, data=data, headers=headers)

        return response.json()
    
    '''
        ticker: 'BTCHKD'
        action: 'bid' or 'ask'
        amount: 0.5
        price: 45406
    '''
    def place_order(self, ticker, action, amount, price):
        data = {'Code': ticker, 'Way': action, 'Amount': str(amount), 'Price': str(price)}
        return self._send_request('Trade/Orders', 'POST', data)
  
  
    def get_balance(self):
        return self._send_request('Balance/Balances', 'GET')
    
    
    ''' Default 1m timeframe for 100 -> 100 mins'''
    def get_ticker_history(self, ticker, timeframe='1m'):
        return self._send_request('Public/TickerHistory/{0}/{1}?Count=100'.format(ticker, timeframe), 'GET')
        
    
    def parseTickerData(self, ticker, tickerData):
        return {'exchange': self.key['exchange'], 'ticker': ticker, 'data': list(map(lambda x: {'price': x['open']}, tickerData['tickers']))}
    
    
if __name__ == "__main__":
    engine = ExchangeEngine()
    engine.load_key('../.keys/gatecoinkey')
    #engine.get_balance()
    print engine.get_ticker_history('BTCHKD', '15m')
    #engine.place_order('BTCHKD', 'bid', 1, 200)
    #engine.place_order('BTCHKD', 'ask', 1, 200)