'''
    All trades have a 0.25% commission. -> real case it is 0.250626606% so use 0.26% for calculation instead

'''

from imports import *

class ExchangeEngine(ExchangeEngineBase):
    def __init__(self):
        self.API_URL = 'https://bittrex.com/api'
        self.apiVersion = 'v1.1'
        self.sleepTime = 5
        self.feeRatio = 0.0026
        self.async = True
                  
    def _send_request(self, command, httpMethod, params={}, hook=None):          
        command = '/{0}/{1}'.format(self.apiVersion, command)

        url = self.API_URL + command
        
        if httpMethod == "GET":
            R = grequests.get
        elif httpMethod == "POST":
            R = grequests.post       
        
        headers = {}
        
        if not any(x in command for x in ['Public', 'public']):
            nonce = str(int(1000*time.time()))
            url = url + '{0}apikey={1}&nonce={2}'.format('&' if '?' in url else '?', self.key['public'], nonce)
            
            secret = self.key['private']
            
            signature = hmac.new(secret.encode('utf8'), url.encode('utf8'), hashlib.sha512)
            signature = signature.hexdigest()
            
            headers = {
                'apisign': signature,
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
        return self._send_request('account/getbalances', 'GET', {}, [self.hook_getBalance(tickers=tickers)])
    
    def hook_getBalance(self, *factory_args, **factory_kwargs):
        def res_hook(r, *r_args, **r_kwargs):
            json = r.json()
            r.parsed = {}
            

            if factory_kwargs['tickers']:
                json['result'] = filter(lambda ticker: ticker['Currency'].upper() in factory_kwargs['tickers'], json['result'])
                
            for ticker in json['result']:
                r.parsed[ticker['Currency'].upper()] = float(ticker['Available'])
                                  
        return res_hook    
    
    '''
        return USDT in r.parsed
        {
            'BTC': 18000    
        }
    '''       
    def get_ticker_lastPrice(self, ticker):
         return self._send_request('public/getticker?market=USDT-{0}'.format(ticker), 'GET', {}, [self.hook_lastPrice(ticker=ticker)])

    def hook_lastPrice(self, *factory_args, **factory_kwargs):
        def res_hook(r, *r_args, **r_kwargs):
            json = r.json()
            r.parsed = {}
            r.parsed[factory_kwargs['ticker']] = json['result']['Last']
                                  
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
        return self._send_request('public/getorderbook?type=both&market={0}'.format(ticker), 'GET', {}, self.hook_orderBook)     
     
    def hook_orderBook(self, r, *r_args, **r_kwargs):
        json = r.json()
        #print json
        r.parsed = {
                    'bid':  {
                             'price': float(json['result']['buy'][0]['Rate']),
                             'amount': float(json['result']['buy'][0]['Quantity'])
                            },
                    'ask':  {
                             'price': float(json['result']['sell'][0]['Rate']),
                             'amount': float(json['result']['sell'][0]['Quantity'])
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
        return self._send_request('market/getopenorders', 'GET', {}, self.hook_openOrder)
    
    def hook_openOrder(self, r, *r_args, **r_kwargs):
        json = r.json()
        r.parsed = []
        for order in json['result']:
            r.parsed.append({'orderId': str(order['OrderUuid']), 'created': order['Opened']})

        
    '''
        ticker: 'ETH-ETC'
        action: 'bid' or 'ask'
        amount: 700
        price: 0.2
    '''
    def place_order(self, ticker, action, amount, price):
        action = 'buy' if action == 'bid' else 'sell'
        if action == 'buy':
            cmd = 'market/buylimit?market={0}&quantity={1}&rate={2}'.format(ticker, amount, price)
        else:
            cmd = 'market/selllimit?market={0}&quantity={1}&rate={2}'.format(ticker, amount, price)
        return self._send_request(cmd, 'GET')    
    
    def cancel_order(self, orderID):
        return self._send_request('market/cancel?uuid={0}'.format(orderID), 'GET')
    
    def withdraw(self, ticker, amount, address):
        return self._send_request('account/withdraw?currency={0}&quantity={1}&address={2}'.format(ticker, amount, address), 'GET')
    
    
if __name__ == "__main__":
    engine = ExchangeEngine()
    engine.load_key('../.keys/bittrexkey')
    # for res in grequests.map([engine.get_ticker_orderBook_innermost('ETH-OMG')]):
    #     print res.parsed
    #     pass
    for res in grequests.map([engine.get_ticker_lastPrice('LTC')]):
        print res.parsed
        pass    
    #print engine.get_ticker_orderBook('ETH-OMG')
    #print engine.parseTickerData(engine.get_ticker_history('XRPUSD'))
    #print engine.place_order('ETH-OMG', 'bid', 10, 0.01)
    #print engine.withdraw('ETH', 500, '0x54A82261bAAc1357069E23d953F8dbC8BD2A54F4')
    #print engine.get_open_order()
    #print engine.cancel_order('9faa6b5b-6709-4435-aec8-fe96f1fa32bb')