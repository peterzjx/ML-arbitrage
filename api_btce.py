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


class tradeapi:
    key = ''
    secret = ''
    nonce = 1;
    wait_for_nonce = False

    def __init__(self, key, secret, wait_for_nonce=False):
        self.key = key
        self.secret = secret
        self.wait_for_nonce = wait_for_nonce
        self.tradeData = {}

    def __nonce(self):
        # if self.wait_for_nonce: time.sleep(1)
        self.nonce = str(int(time.time() * 5) % 4294967296)

    def __sign(self, params):
        return hmac.new(self.secret, params, digestmod=hashlib.sha512).hexdigest()

    def __api_call(self, method, params):
        self.__nonce()
        params['method'] = method
        params['nonce'] = self.nonce
        params = urllib.urlencode(params)
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key": self.key,
                   "Sign": self.__sign(params)}
        try:
            conn = httplib.HTTPSConnection("btc-e.com", timeout=20)
            conn.request("POST", "/tapi", params, headers)
            response = conn.getresponse()
            data = json.load(response)
            conn.close()
            return data
        except Exception as e:
            print "Exception", e
            return None

    def get_param(self, pair, param):
        conn = httplib.HTTPSConnection("btc-e.com")
        conn.request("GET", "/api/2/" + pair + "/" + param)
        response = conn.getresponse()
        data = json.load(response)
        conn.close()
        return data

    def getInfo(self):
        return self.__api_call('getInfo', {})

    def update(self):
        '''Wrapper for get trade information'''
        # sys.stdout.write('-')
        raw = self.getInfo()
        # sys.stdout.write('K')
        if raw == None:
            print ('Error in getInfo')
            time.sleep(5)
            return None
        if raw['success'] == 0:
            print('API response returned status "fail".')
            return None
        output = raw.get('return')
        if output == None:
            print ('output is None')
            return None
        self.tradeData['funds'] = output['funds']
        self.tradeData['openOrders'] = output['open_orders']
        self.tradeData['transCount'] = output['transaction_count']
        self.tradeData['apiRights'] = output['rights']
        self.tradeData['serverTime'] = output['server_time']
        if self.tradeData['openOrders'] > 0:
            self.tradeData['orders'] = self.activeOrders()
        return self.tradeData


    def transHistory(self, tfrom, tcount, tfrom_id, tend_id, torder, tsince, tend):
        params = {
            "from": tfrom,
            "count": tcount,
            "from_id": tfrom_id,
            "end_id": tend_id,
            "order": torder,
            "since": tsince,
            "end": tend}
        return self.__api_call('TransHistory', params)

    def tradeHistory(self, tfrom, tcount, tfrom_id, tend_id, torder, tsince, tend, tpair):
        params = {
            "from": tfrom,
            "count": tcount,
            "from_id": tfrom_id,
            "end_id": tend_id,
            "order": torder,
            "since": tsince,
            "end": tend,
            "pair": tpair}
        return self.__api_call('TradeHistory', params)

    def activeOrders(self, tpair='btc_usd'):
        params = {"pair": tpair}
        return self.__api_call('ActiveOrders', params)

    def trade(self, tpair, ttype, trate, tamount):
        params = {
            "pair": tpair,
            "type": ttype,
            "rate": trate,
            "amount": tamount}
        return self.__api_call('Trade', params)

    def cancelOrder(self, torder_id):
        params = {"order_id": torder_id}
        return self.__api_call('CancelOrder', params)


class publicapi(object):
    '''Parse BTC-e Public API'''

    def __init__(self):
        self.url = 'https://btc-e.com/api/2/'  # append pair, method
        # self.log = logging.getLogger('TickerAPI')
        self.tickerDict = {}

    def update(self, pairs):
        """Updates pairs set to True,
        where pairs is dict of booleans currencies."""
        for pair in pairs:
            if pairs[pair]:
                self.updatePair(pair)
        return self.tickerDict

    def poll(self, url):
        """Generic public API parsing method, returns parsed dict"""
        for i in range(5):
            try:
                request = urllib2.Request(url)
                response = json.loads(urllib2.urlopen(request, timeout=20).read())
                # sys.stdout.write("V")
                return response
            except urllib2.URLError as e:
                print "Caught URL Error, sleeping..."
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

    def ticker(self, pair):
        '''Returns ticker dict for a single pair'''
        url = self.url + pair + '/ticker'
        raw = self.poll(url)
        if raw == None: return None
        ticker = raw['ticker']
        return ticker

    def depth(self, pair):
        '''Returns depth dict for a single pair'''
        url = self.url + pair + '/depth'
        depth = self.poll(url)
        return depth

    def trades(self, pair):
        url = self.url + pair + '/trades'
        trades = self.poll(url)
        return trades

    def getLast(self, pair):
        '''Returns most recent traded price of pair'''
        trades = self.trades(pair)
        price = trades[0].get('price')
        return price

    def getLastID(self, pair):
        '''Returns ID of last trade for pair'''
        trades = self.trades(pair)
        tradeID = trades[0].get('tid')
        return tradeID

    def updatePair(self, pair):
        '''Update stored ticker info for a single pair, reassigns to variables'''
        tick = self.ticker(pair)
        if tick == None: return None
        data = {}
        data['high'] = tick.get('high', 0)
        data['low'] = tick.get('low', 0)
        data['last'] = tick.get('last', 0)
        data['buy'] = tick.get('buy', 0)
        data['sell'] = tick.get('sell', 0)
        data['vol'] = tick.get('vol', 0)
        data['volCur'] = tick.get('vol_cur', 0)
        data['avg'] = tick.get('avg', 0)
        # uncomment depth/trades for gigantic dict
        # data['depth'] = self.depth(pair)
        # data['trades'] = self.trades(pair)
        self.tickerDict[pair] = data
        return self.tickerDict[pair]