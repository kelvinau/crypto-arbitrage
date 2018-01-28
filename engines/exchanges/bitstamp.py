'''
    All trades have a 0.25% commission. -> real case it is 0.250626606% so use 0.26% for calculation instead

'''

from mod_imports import *

class ExchangeEngine(ExchangeEngineBase):
    def __init__(self):
        self.API_URL = 'https://www.bitstamp.net/api'
        self.apiVersion = 'v2'
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
        
        if httpMethod == "POST":
            nonce = int(1000*time.time())
            message = str(nonce) + self.key['customer_id'] + self.key['public']
 
            signature = hmac.new(
                self.key['private'].encode('utf8'),
                msg=message.encode('utf8'),
                digestmod=hashlib.sha256
            ).hexdigest().upper()
            params['key'] = self.key['public']
            params['nonce'] = nonce
            params['signature'] = signature
            
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
        return self._send_request('balance/', 'POST', {}, [self.hook_getBalance(tickers=tickers)])
    
    def hook_getBalance(self, *factory_args, **factory_kwargs):
        def res_hook(r, *r_args, **r_kwargs):
            json = r.json()
            r.parsed = {}
            suffix = '_available'

            if factory_kwargs['tickers']:
                for ticker in factory_kwargs['tickers']:
                    r.parsed[ticker] = float(json[ticker + suffix])
            else:
                for k, v in json.iteritems():
                    if suffix in k:
                        ticker = k.split(suffix)[0]
                        r.parsed[ticker] = float(v)
                                     
        return res_hook    

    '''
        return USDT in r.parsed
        {
            'BTC': 18000    
        }
    '''       
    def get_ticker_lastPrice(self, ticker):
         return self._send_request('ticker/{0}/'.format(ticker), 'GET', {}, [self.hook_lastPrice(ticker=ticker)])

    def hook_lastPrice(self, *factory_args, **factory_kwargs):
        def res_hook(r, *r_args, **r_kwargs):
            json = r.json()
            r.parsed = {}
            r.parsed[factory_kwargs['ticker']] = float(json['last'])
                                  
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
        return self._send_request('order_book/{0}/'.format(ticker), 'GET', {}, self.hook_orderBook)     
     
    def hook_orderBook(self, r, *r_args, **r_kwargs):
        json = r.json()
        #print json
        r.parsed = {
                    'bid':  {
                             'price': float(json['bids'][0][0]),
                             'amount': float(json['bids'][0][1])
                            },
                    'ask':  {
                             'price': float(json['asks'][0][0]),
                             'amount': float(json['asks'][0][1])
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
        return self._send_request('open_orders/all/', 'POST', {}, self.hook_openOrder)
    
    def hook_openOrder(self, r, *r_args, **r_kwargs):
        json = r.json()
        print json
        r.parsed = []
        for order in json:
            r.parsed.append({'orderId': str(order['id']), 'created': order['datetime']})

        
    '''
        ticker: 'ETH-ETC'
        action: 'bid' or 'ask'
        amount: 700
        price: 0.2
    '''
    def place_order(self, tickerPair, action, amount, price):
        action = 'buy' if action == 'bid' else 'sell'
        cmd = '{0}/{1}/'.format(action, tickerPair)
        return self._send_request(cmd, 'POST', {"amount": amount, "price": price})    
    
    def cancel_order(self, orderID):
        return self._send_request('cancel_order/', 'POST', {"id": orderID})
    
    def withdraw(self, ticker, amount, address):
        if ticker == 'btc':
            urlPart = 'bitcoin_withdrawal'
        elif ticker == 'eth':
            urlPart = 'eth_withdrawal'
        elif ticker == 'ltc':
            ulrPart = 'ltc_withdrawal'
        elif ticker == 'xrp':
            urlPart = 'ripple_withdrawal'
        else:
            raise Exception('{0} is not implemented for withdrawal'.format(ticker))
        return self._send_request('{0}/'.format(urlPart), 'POST', {"amount": amount, "address": address})
    
if __name__ == "__main__":
    engine = ExchangeEngine()
    engine.load_key('../../keys/bitstamp.key')
    # for res in grequests.map([engine.get_balance(['btc', 'eth'])]):
    #     print res.parsed
    #     pass    
    for res in grequests.map([engine.get_ticker_lastPrice('btcusd')]):
        print res.parsed
    pass    
    # for res in grequests.map([engine.get_ticker_orderBook_innermost('ethbtc')]):
    #     print res.parsed
    #     pass
    # for res in grequests.map([engine.get_open_order()]):
    #     print res.parsed
    #     pass    
    # for res in grequests.map([engine.place_order("ethbtc", "ask", 0.5, 0.5)]):
    #     print res.json()
    #     #print res.parsed/
    #     pass    
    # for res in grequests.map([engine.cancel_order('624731173')]):
    #     print res.json()
    #     #print res.parsed
    #     pass       
    # for res in grequests.map([engine.withdraw('eth', 500, '0xC257274276a4E539741Ca11b590B9447B26A8051')]):
    #     print res.json()
    #     #print res.parsed
    #     pass       