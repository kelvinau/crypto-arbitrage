'''
EXECUTED IN THE LAST 30 DAYS (USD EQUIVALENT)    MAKER FEES    TAKER FEES
$0.00 or more traded                               0.100%        0.200%
$500,000.00 or more traded                         0.080%        0.200%
$1,000,000.00 or more traded                       0.060%        0.200%
$2,500,000.00 or more traded                       0.040%        0.200%
$5,000,000.00 or more traded                       0.020%        0.200%
$7,500,000.00 or more traded                       0.000%        0.200%
$10,000,000.00 or more traded                      0.000%        0.180%
$15,000,000.00 or more traded                      0.000%        0.160%
$20,000,000.00 or more traded                      0.000%        0.140%
$25,000,000.00 or more traded                      0.000%        0.120%
$30,000,000.00 or more traded                      0.000%        0.100%
'''

from mod_imports import *
class ExchangeEngine(ExchangeEngineBase):
    def __init__(self):
        self.API_URL = 'https://api.bitfinex.com'
        self.apiVersion = 'v1'
        self.sleepTime = 5
        self.feeRatio = 0.002
        self.async = True
        
    def _send_request(self, command, httpMethod, params={}, hook=None):          
        command = '/{0}/{1}'.format(self.apiVersion, command)

        url = self.API_URL + command
        headers = {}
        if httpMethod == "GET":
            R = grequests.get
        elif httpMethod == "POST":
            R = grequests.post          
            
            secret = self.key['private']
            params['request'] = command
            params['nonce'] = str(long(1000000*time.time()))
            
            j = json.dumps(params)
            message = base64.standard_b64encode(j.encode('utf8'))
            
            signature = hmac.new(secret.encode('utf8'), message, hashlib.sha384)
            signature = signature.hexdigest()
            
            headers = {
                'X-BFX-APIKEY': self.key['public'],
                'X-BFX-PAYLOAD': message,
                'X-BFX-SIGNATURE': signature
            }       
               
        args = {'data': params, 'headers': headers}
        if hook:
            args['hooks'] = dict(response=hook)
            
        req = R(url, **args)
        if self.async:
            return req
        else:
            response = grequests.map([req])[0].json()
            
            if 'error' in response:
                print response
            return response    
    
    
    '''
        return in r.parsed, showing all and required tickers
        {
            'ETH': 0.005,
            'OMG': 0
        }
    '''
    def get_balance(self, tickers=[]):
        return self._send_request('balances', 'POST', {}, [self.hook_getBalance(tickers=tickers)])
    
    def hook_getBalance(self, *factory_args, **factory_kwargs):
        def res_hook(r, *r_args, **r_kwargs):
            json = r.json()
            r.parsed = {}
            
            if factory_kwargs['tickers']:
                json = filter(lambda ticker: ticker['currency'].upper() in factory_kwargs['tickers'], json)
                
            for ticker in json:
                r.parsed[ticker['currency'].upper()] = float(ticker['amount'])
                    
                                  
        return res_hook    


    '''
        return in r.parsed
        {
            'bid': {
                'price': 0.02202,
                'amount': 1103.5148
            },
            'ask': {
                'price': 0.02400,
                'amount': 103.2
            },           
        }
    '''
    def get_ticker_orderBook_innermost(self, ticker): 
        return self._send_request('book/{0}'.format(ticker), 'GET', {}, self.hook_orderBook)  
    
    def hook_orderBook(self, r, *r_args, **r_kwargs):
        json = r.json()
        r.parsed = {
                    'bid':  {
                             'price': float(json['bids'][0]['price']),
                             'amount': float(json['bids'][0]['amount'])
                            },
                    'ask':  {
                             'price': float(json['asks'][0]['price']),
                             'amount': float(json['asks'][0]['amount'])
                            }
                    }
    
    '''
        return in r.parsed
        [
            {
                'orderId': 1242424
            }
        ]
    '''        
    def get_open_order(self):
        return self._send_request('orders', 'POST', {}, self.hook_openOrder) 
       
    def hook_openOrder(self, r, *r_args, **r_kwargs):
        json = r.json()
        r.parsed = []
        for order in json:
            r.parsed.append({'orderId': order['id'], 'created': order['timestamp']})
        
    '''
        ticker: 'OMGETH'
        action: 'bid' or 'ask'
        amount: 700
        price: 0.2
    '''
    def place_order(self, ticker, action, amount, price):
        action = 'buy' if action == 'bid' else 'sell'
        data = {'symbol': ticker, 'side': action, 'amount': str(amount), 'price': str(price), 'exchange': 'bitfinex', 'type': 'exchange limit'}
        return self._send_request('order/new', 'POST', data)
  
    def cancel_order(self, orderID):
        return self._send_request('order/cancel', 'POST', {'order_id': long(orderID)})    
    
    
    
    ''' bitfinex doesn't provide external withdrawal api
    def withdraw(self, amount, address):
        data = {'withdraw_type': 'OMG', 'walletselected': 'exchange', 'amount': amount, 'address': address}
        return self._send_request('account_infos', data)
    '''
    
   
    
if __name__ == "__main__":
    engine = ExchangeEngine()
    engine.load_key('../.keys/bitfinexkey')
    #print engine.get_balance()

    for res in grequests.map([engine.cancel_order('525113932211')]):
        print res.json()
        pass    

#     for res in grequests.map([engine.place_order('OMGETH', 'bid', 5, 0.02)]):
#         print res.json()
#         pass
#        
    #print engine.get_open_order()
    #engine.place_order('OMGETH', 'bid', 40, 0.01)
    #print engine.get_ticker_orderBook('OMGETH')
    #print engine.place_order('OMGETH', 'bid', 850, 0.02)
    #print engine.cancel_order(446915287)