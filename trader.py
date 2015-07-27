# import helper
import api_btce
import api_stamp

import time
import logging
import datetime
import pickle
import sys
import simulator


class trader(object):
    def __init__(self, arg):
        self.arg = arg
        self.simMode = arg.get('simMode', 1)
        self.config = arg.get('config', None)
        self.breakpoint = arg.get('breakpoint', None)
        self.plot = arg.get('plot', None)
        self.log = logging.getLogger('trader')

        self.tick_btce = api_btce.publicapi()
        self.tick_stamp = api_stamp.publicapi()

        if self.simMode != 0:
            self.tapi_btce = api_btce.tradeapi(self.config.apikey_btce, self.config.apisecret_btce)
            self.tapi_stamp = api_stamp.tradeapi(self.config.apikey_stamp, self.config.apisecret_stamp, self.config.apiid_stamp)

            self.hr_btce = historyRecorder(self.arg, "btce")
            self.hr_stamp = historyRecorder(self.arg, "stamp")
        else:
            self.hr_btce = simulator.simHistoryRecorder(self.arg, "btce")
            self.hr_stamp = simulator.simHistoryRecorder(self.arg, "stamp")
            self.sim_btce = simulator.simulator("btce", {"usd": 0, "btc": 1}, self.arg, self.hr_btce, 0.002)
            self.sim_stamp = simulator.simulator("stamp", {"usd": 500, "btc": 0}, self.arg, self.hr_stamp, 0.005)

    def update(self):
        self.hr_btce.append(self.getOrderEdge("btce"))
        self.hr_stamp.append(self.getOrderEdge("stamp"))

    def getOrderEdge(self, exchange):
        """return [time, bid1 price, bid1 vol, ask1 price, ask1 vol]"""
        dict = {}
        orderbook = {}
        if exchange == "btce":
            orderbook = self.tick_btce.depth("btc_usd")
        elif exchange == "stamp":
            orderbook = self.tick_stamp.depth()
        else:
            print "Stock name error"
        try:
            dict['timestamp'] = int(time.time())
            dict['bid1'] = [float(x) for x in orderbook['bids'][0]]
            dict['ask1'] = [float(x) for x in orderbook['asks'][0]]
        except Exception as e:
            print "Exception", e
            return None
        data = (dict['timestamp'], dict['bid1'][0], dict['bid1'][1], dict['ask1'][0], dict['ask1'][1])
        # print "exchange", exchange, data
        return data

    def getBalance(self, exchange):
        """return a dict of {"btc": 0, "usd": 0}"""
        balance = {"btc": 0, "usd": 0}
        try:
            if exchange == "btce":
                result = self.tapi_btce.update()
                funds = result.get('funds', None)
                balance["btc"] = float(funds.get('btc', 0))
                balance["usd"] = float(funds.get('usd', 0))
            elif exchange == "stamp":
                result = self.tapi_stamp.account_balance()
                balance["btc"] = float(result.get('btc_balance', 0))
                balance["usd"] = float(result.get('usd_balance', 0))
            else:
                balance1 = self.getBalance("btce")
                balance2 = self.getBalance("stamp")
                balance["btc"] = balance1["btc"] + balance2["btc"]
                balance["usd"] = balance1["usd"] + balance2["usd"]
            return balance
        except Exception as e:
           print "Exception", e
        print exchange, balance
        return balance

    def placeOrder(self, orderType, rate, amount, seconds = 0, exchange=""):
        if seconds == 0:
            seconds = 60
        if exchange == "btce":
            pair = "btc_usd"
            if amount < 0.1:  # can't trade < 0.1
                # self.log.warning('Attempted order below 0.1: %s' % amount)
                print "attempted order below 0.1"
                return False
            else:
                # self.log.info('Placing order')
                print "placing order"
                time.sleep(1)
                rate = round(rate, 3)
                response = self.tapi_btce.trade(pair, orderType, rate, amount)
                if response is None:
                    print "Place Order Error"
                    return None
                if response['success'] == 0:
                    response = response['error']
                    # self.log.critical('Order returned error:/n %s' % response)
                    print ('Order returned error:/n %s' % response)
                    return False
                elif response.get('return').get('remains') == 0:
                    # self.log.debug('Trade Result: %s' % response)
                    print ('Trade Result: %s' % response)
                    return True
                else:
                    response = response['return']
                    # self.trackOrder(response, self.config.pair, orderType, rate, seconds)
                    # self.log.info('Order Placed, awaiting fill: %s' % (response))
                    print "Order placed awaiting fill"
                    # self.log.info('Start tracking Orders')
                    # self.needTrackOrders = True
                    return True
        elif exchange == "stamp":
            if amount * rate < 5:  # can't trade < 0.1
                # self.log.warning('Attempted order below 0.1: %s' % amount)
                print "attempted order below $5"
                return False
            else:
                # self.log.info('Placing order')
                time.sleep(1)
                rate = round(rate, 3)
                if orderType == 'buy':
                    response = self.tapi_stamp.buy_limit_order(amount, rate)
                elif orderType == 'sell':
                    response = self.tapi_stamp.sell_limit_order(amount, rate)
                else:
                    response = None
                    print "order Type error"
                print response
                # self.trackOrder(response, self.config.pair, orderType, rate, seconds)
                # self.log.info('Order Placed, awaiting fill: %s' % (response))
                # self.log.info('Start tracking Orders')
                # self.needTrackOrders = True
                print "Order placed awaiting fill"
                return True
        else:
            print "Stock name error"

    # def getTradeAmount(self, exchange, orderType):
    #     balanceDict = self.getBalance(exchange)
    #     orderEdge = self.getOrderEdge(exchange)
    #     amount = 0
    #     max_amount = 0
    #     if orderType == "buy":
    #         rate, amount = orderEdge[3], orderEdge[4] # lowest ask price and vol
    #         balance = balanceDict['usd']
    #         max_amount = round((balance / rate), 8) - 0.0005
    #     if orderType == "sell":
    #         rate, amount = orderEdge[1], orderEdge[2] # higest bid price and vol
    #         balance = balanceDict['btc']
    #         max_amount = round(balance, 8) - 0.0005
    #     return min(amount, max_amount)

    def trade(self, exchange, orderType, amount, rate=0, suggested_rate = 0, seconds=0):
        if self.simMode == 0:
            if exchange == "btce":
                current_rate = float(self.hr_btce.getValue()[1]) #todo: not 1?
                sim = self.sim_btce
            elif exchange == "stamp":
                current_rate = float(self.hr_stamp.getValue()[1])
                sim = self.sim_stamp
            else:
                print "exchange error"
                return False

            if rate == 0:
                rate = current_rate
            # if percentage != 0:
            #     amount = sim.usd * percentage / rate
            #     amount = max(0.1, amount)
            if orderType == "buy":#todo: combine them to trade
                sim.buy(rate, amount)
            else:
                sim.sell(rate, amount)
            return True

        ### real trading
        isPriceDeviated = False

        if rate == 0:
            isMarketOrder = True
        else:
            isMarketOrder = False

        if isMarketOrder:
            orderEdge = self.getOrderEdge(exchange)
            if orderType == "buy":
                rate, rawamount = orderEdge[3], orderEdge[4] # lowest ask price and vol
                if abs(suggested_rate - rate) > 1:
                    isPriceDeviated = True
            if orderType == "sell":
                rate, rawamount = orderEdge[1], orderEdge[2] # higest bid price and vol
                if abs(suggested_rate - rate) > 1:
                    isPriceDeviated = True

        if isPriceDeviated:
            print('Suggested rate %s, actual rate %s, order cancelled.' % (str(suggested_rate), str(rate)))
            return False

        if exchange == "btce":
            min_amount = 0.1
        elif exchange == "stamp":
            min_amount = 5 / float(rate)
        else:
            min_amount = 0
        if amount < min_amount:
            print ("not enough money or coin to %s %s" % (orderType, str(amount)))
            return False

        amount = round(amount, 3)

        if self.simMode == 1:
            #self.log.info('SimMode: buy: %s vol %s' % (rate, amount))
            print "simMode"
        elif self.simMode == 2:
            #self.log.info('Attempted buy: %s %s vol %s' % (pair, rate, amount))
            self.log.info('%s Attempted %s: %s vol %s' % (exchange, orderType, rate, amount))
            isOrderSuccess = self.placeOrder(orderType, rate, amount, seconds, exchange)
            if isOrderSuccess:
                #self.log.info('Order successfully placed')
                print ('Order successfully placed')
                return True
            else:
                #self.log.info('Order placing failed')
                print ('Order placing failed')
                return False

    def openOrders(self, exchange):
        if exchange == "btce":
            raw = self.tapi_btce.activeOrders()
            if raw is None:
                print "ActiveOrder is None"
            return raw.get('return', {})
        elif exchange == "stamp":
            raw = self.tapi_stamp.open_orders()
            return raw
        else:
            print "exchange name error"
            return None

    def isAllOrderClosed(self):
        try:
            openOrders_btce = self.openOrders("btce")
            openOrders_stamp = self.openOrders("stamp")
            if openOrders_btce is None or openOrders_stamp is None:
                return False
            else:
                return len(openOrders_stamp) == 0 and len(openOrders_btce) == 0
        except Exception, e:
            print e
    def killAll(self, exchange):
        if exchange == "btce":
            raw = self.tapi_btce.activeOrders()
            if raw is None:
                print "ActiveOrder is None"
            updatedOrders = raw.get('return', {})
            for orderID in updatedOrders.keys():
                raw = self.tapi_btce.cancelOrder(orderID)
                if raw is None:
                    print "Cancelling error"
                    return False
                print "Cancelling Success"
                time.sleep(1)
        elif exchange == "stamp":
            raw = self.tapi_stamp.open_orders()
            for dict in raw:
                raw = self.tapi_stamp.cancel_order(dict["id"])
                if not raw:
                    print "Cancel error"
                    return False
                print "Cancel success"
        else:
            print "exchange name error"
            return False
        return True


class historyRecorder(object):
    def __init__(self, arg, exchange):
        self.arg = arg
        self.simMode = arg.get('simMode', 1)
        self.config = arg.get('config', None)
        self.breakpoint = arg.get('breakpoint', None)
        self.plot = arg.get('plot', None)

        self.exchange = exchange
        self.data = []
        self.single = []

        # get save file name
        if self.exchange == "btce":
            self.savefile = self.config.savefile_btce
        elif self.exchange == "stamp":
            self.savefile = self.config.savefile_stamp

        self.load()

    def save(self):
        if self.savefile:
            with open(self.savefile, 'wb') as f:
                pickle.dump(self.data, f)
                print "Save", self.savefile

    def load(self):
        try:
            f = open(self.savefile, 'rb')
            self.data = pickle.load(f)[-10000:]
            print self.data[-1]
            print "Current length of data depth", self.savefile, len(self.data)
            f.close()
        except (IOError, TypeError, EOFError), e:
            print 'Load price info error'
            print e

    def append(self, item):
        """
        item = (int[timestamp], float['bid1'][price], float['bid1'][volume], float['ask1'][price], float['ask1'][volume])
        """

        self.data.append(item)

    def getData(self):
    #     '''Now uses close price, change to weighted average in the future'''
    #     '''Change to constantly updating version'''
        return self.data
    #
    def getValue(self):
        return self.data[-1]