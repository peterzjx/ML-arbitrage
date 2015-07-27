import hashlib
import hmac
import json
import time
import httplib
import urllib
import urllib2
import helper
import logging
import sys
import requests

class tradeapi:
    key = ''
    secret = ''
    nonce = 1
    wait_for_nonce = False

    def __init__(self, key, secret, id, wait_for_nonce = False):
        self.key = key
        self.secret = secret
        self.id = id
        self.wait_for_nonce = wait_for_nonce
        self.tradeData = {}
    
    def _nonce(self):
        if self.wait_for_nonce: time.sleep(1)
        self.nonce = str(int(time.time() * 5) % 4294967296)
        #self.nonce = str(int(time.time()))

    def _default_data(self, *args, **kwargs):
        """
        Generate a one-time signature and other data required to send a secure
        POST request to the Bitstamp API.
        """
        data = {}
        data['key'] = self.key
        self._nonce()
        nonce = self.nonce
        msg = str(nonce) + self.id + self.key

        signature = hmac.new(
            self.secret.encode('utf-8'), msg=msg.encode('utf-8'),
            digestmod=hashlib.sha256).hexdigest().upper()
        data['signature'] = signature
        data['nonce'] = nonce
        return data
        
    def _post(self, *args, **kwargs):
        """
        Make a POST request.
        """
        data = self._default_data()
        data.update(kwargs.get('data') or {})
        kwargs['data'] = data
        return self._request(requests.post, *args, **kwargs)

    def _request(self, func, url, *args, **kwargs):
        """
        Make a generic request, adding in any proxy defined by the instance.

        Raises a ``requests.HTTPError`` if the response status isn't 200, and
        raises a :class:`BitstampError` if the response contains a json encoded
        error message.
        """
        return_json = kwargs.pop('return_json', False)
        url = "https://www.bitstamp.net/api/" + url
        response = func(url, *args, **kwargs)

        # Check for error, raising an exception if appropriate.
        response.raise_for_status()

        try:
            json_response = response.json()
        except ValueError:
            json_response = None
        if isinstance(json_response, dict):
            error = json_response.get('error')
            if error:
                print "error json responce is not dict"

        if return_json:
            if json_response is None:
                print "Error json response is none"
            return json_response

        return response
        
    # Trading api
        
    def account_balance(self):
        """
        Returns dictionary::

            {u'btc_reserved': u'0',
             u'fee': u'0.5000',
             u'btc_available': u'2.30856098',
             u'usd_reserved': u'0',
             u'btc_balance': u'2.30856098',
             u'usd_balance': u'114.64',
             u'usd_available': u'114.64'}
        """
        #return self.__api_call("balance")
        return self._post("balance/", return_json=True)

    def user_transactions(self, offset=0, limit=100, descending=True):
        """
        Returns descending list of transactions. Every transaction (dictionary)
        contains::

            {u'usd': u'-39.25',
             u'datetime': u'2013-03-26 18:49:13',
             u'fee': u'0.20', u'btc': u'0.50000000',
             u'type': 2,
             u'id': 213642}
        """
        data = {
            'offset': offset,
            'limit': limit,
            'sort': 'desc' if descending else 'asc',
        }
        return self._post("user_transactions/", data=data, return_json=True)

    def open_orders(self):
        """
        Returns JSON list of open orders. Each order is represented as a
        dictionary.
        """
        return self._post("open_orders/", return_json=True)

    def cancel_order(self, order_id):
        """
        Cancel the order specified by order_id.

        Returns True if order was successfully canceled,otherwise raise a
        BitstampError.
        """
        data = {'id': order_id}
        return self._post("cancel_order/", data=data, return_json=True)

    def buy_limit_order(self, amount, price):
        """
        Order to buy amount of bitcoins for specified price.
        """
        data = {'amount': amount, 'price': price}

        return self._post("buy/", data=data, return_json=True)

    def sell_limit_order(self, amount, price):
        """
        Order to buy amount of bitcoins for specified price.
        """
        data = {'amount': amount, 'price': price}
        return self._post("sell/", data=data, return_json=True)

    def check_bitstamp_code(self, code):
        """
        Returns JSON dictionary containing USD and BTC amount included in given
        bitstamp code.
        """
        data = {'code': code}
        return self._post("check_code/", data=data, return_json=True)

    def redeem_bitstamp_code(self, code):
        """
        Returns JSON dictionary containing USD and BTC amount added to user's
        account.
        """
        data = {'code': code}
        return self._post("redeem_code/", data=data, return_json=True)

    def withdrawal_requests(self):
        """
        Returns list of withdrawal requests.

        Each request is represented as a dictionary.
        """
        return self._post("withdrawal_requests/", return_json=True)

    def bitcoin_withdrawal(self, amount, address):
        """
        Send bitcoins to another bitcoin wallet specified by address.
        """
        data = {'amount': amount, 'address': address}
        return self._post("bitcoin_withdrawal/", data=data, return_json=True)

    def bitcoin_deposit_address(self):
        """
        Returns bitcoin deposit address as unicode string
        """
        return self._post("bitcoin_deposit_address/", return_json=True)

    def unconfirmed_bitcoin_deposits(self):
        """
        Returns JSON list of unconfirmed bitcoin transactions.

        Each transaction is represented as dictionary:

        amount
          bitcoin amount
        address
          deposit address used
        confirmations
          number of confirmations
        """
        return self._post("unconfirmed_btc/", return_json=True)
    
    # def get_param(self, pair, param):
        # conn = httplib.HTTPSConnection("btc-e.com")
        # conn.request("GET", "/api/"+param)
        # response = conn.getresponse()
        # data = json.load(response)
        # conn.close()
        # return data
    
    # def getInfo(self):
        # return self.__api_call('getInfo', {})
    
    # def update(self):
        # '''Wrapper for get trade information'''
        # # sys.stdout.write('-')
        # raw = self.getInfo()
        # # sys.stdout.write('K')
        # if raw == None:
            # print ('Error in getInfo')
            # time.sleep(5)
            # return None
        # if raw['success'] == 0:
            # print('API response returned status "fail".')
            # return None
        # output = raw.get('return')
        # if output == None:
            # print ('output is None')
            # return None
        # self.tradeData['funds'] = output['funds']
        # self.tradeData['openOrders'] = output['open_orders']
        # self.tradeData['transCount'] = output['transaction_count']
        # self.tradeData['apiRights'] = output['rights']
        # self.tradeData['serverTime'] = output['server_time']
        # if self.tradeData['openOrders'] > 0:
            # self.tradeData['orders'] = self.activeOrders()
        # return self.tradeData 
        
    
    # def transHistory(self, tfrom, tcount, tfrom_id, tend_id, torder, tsince, tend):
        # params = {
           # "from" : tfrom,
           # "count"    : tcount,
           # "from_id"  : tfrom_id,
           # "end_id"   : tend_id,
           # "order"    : torder,
           # "since"    : tsince,
           # "end"  : tend}
        # return self.__api_call('TransHistory', params)
 
    # def tradeHistory(self, tfrom, tcount, tfrom_id, tend_id, torder, tsince, tend, tpair):
        # params = {
           # "from" : tfrom,
           # "count"    : tcount,
           # "from_id"  : tfrom_id,
           # "end_id"   : tend_id,
           # "order"    : torder,
           # "since"    : tsince,
           # "end"  : tend,
           # "pair" : tpair}
        # return self.__api_call('TradeHistory', params)

    # def activeOrders(self, tpair = 'btc_usd'):
        # params = { "pair" : tpair }
        # return self.__api_call('ActiveOrders', params)

    # def trade(self, tpair, ttype, trate, tamount):
        # params = {
            # "pair"    : tpair,
            # "type"    : ttype,
            # "rate"    : trate,
            # "amount": tamount}
        # return self.__api_call('Trade', params)
  
    # def cancelOrder(self, torder_id):
        # params = { "order_id" : torder_id }
        # return self.__api_call('CancelOrder', params)

class publicapi(object):
    '''Parse BTC-e Public API'''
        
    def __init__(self):
        self.url = 'https://www.bitstamp.net/api/' #append pair, method
        #self.log = logging.getLogger('TickerAPI')
        self.tickerDict = {}
        
    def update(self,pairs):
        '''Updates pairs set to True,
        where pairs is dict of booleans currencies.'''
        for pair in pairs:
            if pairs[pair]:
                self.updatePair(pair)
        return self.tickerDict 

    def poll(self,url):
        '''Generic public API parsing method, returns parsed dict'''
        for i in range(5):
            try:
                request = urllib2.Request(url)
                response = json.loads(urllib2.urlopen(request, timeout = 20).read())
                # sys.stdout.write("V")
                return response
            except urllib2.URLError as e:
                print "Caught URL Error, sleeping..."
                for second in range(5):
                    time.sleep(1) 
                print "Retrying connection now."
                continue
            except urllib2.HTTPError as e:
                print "Caught HTTP Error, sleeping..."
                for second in range(5):
                    time.sleep(1) 
                print "Retrying connection now."
                continue
            except Exception as e:
                print 'publicapi.poll caught other Exception:'
                print e
                print 'Sleeping...'
                for second in range(5):
                    time.sleep(1) 
                print "Retrying now."
                continue
        print "Unknown Error in publicapi poll"
        return None
    # def ticker(self,pair):
        # '''Returns ticker dict for a single pair'''
        # url = self.url + pair + '/ticker'
        # raw = self.poll(url)
        # if raw == None: return None
        # ticker = raw['ticker']
        # return ticker

    def depth(self):
        '''Returns depth dict for a single pair'''
        url = self.url + 'order_book/'
        depth = self.poll(url)
        return depth

    # def trades(self,pair):
        # url = self.url + pair + '/trades'
        # trades = self.poll(url)
        # return trades

    # def getLast(self,pair):
        # '''Returns most recent traded price of pair'''
        # trades = self.trades(pair)
        # price = trades[0].get('price')
        # return price

    # def getLastID(self,pair):
        # '''Returns ID of last trade for pair'''
        # trades = self.trades(pair)
        # tradeID = trades[0].get('tid')
        # return tradeID
        
    # def updatePair(self,pair):
        # '''Update stored ticker info for a single pair, reassigns to variables'''
        # tick = self.ticker(pair)
        # if tick == None: return None
        # data = {}
        # data['high'] = tick.get('high',0)
        # data['low'] = tick.get('low',0)
        # data['last'] = tick.get('last',0)
        # data['buy'] = tick.get('buy',0)
        # data['sell'] = tick.get('sell',0)
        # data['vol'] = tick.get('vol',0)
        # data['volCur'] = tick.get('vol_cur',0)
        # data['avg'] = tick.get('avg',0)
        # # uncomment depth/trades for gigantic dict
        # #data['depth'] = self.depth(pair)
        # #data['trades'] = self.trades(pair)
        # self.tickerDict[pair] = data
        # return self.tickerDict[pair]