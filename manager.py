import time
import logging
from datetime import datetime
import sys
import trader


class Manager(object):
    def __init__(self, arg):
        self.arg = arg
        self.simMode = arg.get('simMode', 1)
        self.config = arg.get('config', None)
        self.breakpoint = arg.get('breakpoint', None)
        self.plot = arg.get('plot', None)

        self.fee1 = 1.002
        self.fee2 = 1.0024

        self.moveAmount = 6.0
        self.moveStep = 2.0
        self.moveAmountPosition = 0

        self.log = logging.getLogger('manager')

        self.isCurrentActionDone = True
        self.currentDecision = {}

        self.trader = trader.trader(arg)
        self.initStrategy()

    # def runOnce(self):
    # amount = self.getMoveAmount(False)
    #     self.move(amount, False)

    def runLoop(self):
        interval = 10  # 1 min for real trading
        nextTriggerTime = time.time() + 15 * interval
        self.log.info("Loop start" + str(self.trader.getBalance("all")) + " btce " + str(
            self.trader.getBalance("btce")) + " stamp " + str(self.trader.getBalance("stamp")))
        self.updateMoveAmountPosition()
        while True:
            self.trader.update()
            self.updateStrategy()

            if not self.isCurrentActionDone:  # if there are unclosed orders
                if self.trader.isAllOrderClosed():  # check if they are closed
                    self.isCurrentActionDone = True
                    self.log.info(self.currentDecision.get('action', 'None') + str(
                        self.trader.getBalance("all")) + " btce " + str(
                        self.trader.getBalance("btce")) + " stamp " + str(self.trader.getBalance("stamp")))
                    self.updateMoveAmountPosition()
                else:  # if not, kill them
                    self.trader.killAll("btce")
                    self.trader.killAll("stamp")
                    time.sleep(5)

                    self.makeDecision(self.currentDecision)  #TODO: smarter control of resubmit decision

            if self.isCurrentActionDone:
                self.currentDecision = self.strategyList["Diff Comparer"].decision
                self.makeDecision(self.currentDecision)
            timer = time.time()
            sys.stdout.write(".")
            time.sleep(interval)

            if timer >= nextTriggerTime:
                nextTriggerTime += 15 * interval
                sys.stdout.write(",")
                self.trader.hr_btce.save()
                self.trader.hr_stamp.save()


    def runLoopSim(self):
        self.trader.hr_btce.start()
        self.trader.hr_stamp.start()
        self.initStrategy()
        while True:
            isRunning = self.trader.hr_btce.start() and self.trader.hr_stamp.start()
            if not isRunning:
                break
            # print self.hr.getValue()
            self.updateStrategy()
            self.currentDecision = self.strategyList["Diff Comparer"].decision
            self.makeDecision(self.currentDecision)
            self.startStrategy()


    def makeDecision(self, decision):
        if decision != {}:
            action = decision.get('action', None)
            self.currentDecision = decision
            if action == "left":
                self.moveToDirection(isLeft=True)
                time.sleep(10)
            elif action == "right":
                self.moveToDirection(isLeft=False)
                time.sleep(10)
            else:
                print "make Decision error"
                return False


# def getMoveAmount(self, isLeft=True):
# """return the maxmium amount of coins available for moving, after fee"""
#     balance_btce = self.trader.getBalance("btce")
#     balance_stamp = self.trader.getBalance("stamp")
#     if isLeft:
#         '''buy coin in stamp, sell coin in btce'''
#         # look at ask (sell) price in stamp, bid (buy) price in btce
#         edge_stamp = self.trader.getOrderEdge("stamp")
#         buy_price = edge_stamp[3]
#         min_buy_amount = float(balance_stamp['usd']) / buy_price
#         # sell_price = edge_btce[1]
#         min_sell_amount = float(balance_btce['btc'])
#         amount = min(min_buy_amount * 0.995, min_sell_amount)
#     else:
#         '''buy coin in btce, sell coin in stamp'''
#         # look at ask (sell) price in btce, bid (buy) price in stamp
#         edge_btce = self.trader.getOrderEdge("btce")
#         buy_price = edge_btce[3]
#         min_buy_amount = float(balance_btce['usd']) / buy_price
#         # sell_price = edge_btce[1]
#         min_sell_amount = float(balance_stamp['btc'])
#         amount = min(min_buy_amount * 0.998, min_sell_amount)
#     return amount

def updateMoveAmountPosition(self):
    """return the current position of amount of coins available for moving, after fee, in terms of btce coin amount"""
    balance_btce = self.trader.getBalance("btce")
    # balance_stamp = self.trader.getBalance("stamp")
    pos = float(balance_btce['btc']) - 0.1
    print "Pos", pos
    self.moveAmountPosition = self.moveStep * round(pos / self.moveStep)
    return self.moveAmountPosition


def moveToDirection(self, isLeft=True):
    """Call moveToTarget"""
    current_pos = self.moveAmountPosition
    print "Current Position", current_pos
    if isLeft:  # Left
        target_btce = max(current_pos - self.moveStep, 0) + 0.1
        target_stamp = min(self.moveAmount - current_pos + self.moveStep, self.moveAmount) + 0.1
    else:  # Right
        target_btce = min(current_pos + self.moveStep, self.moveAmount) + 0.1
        target_stamp = max(self.moveAmount - current_pos - self.moveStep, 0) + 0.1
    target = {'btce': target_btce, 'stamp': target_stamp}
    self.moveToTarget(target)


def moveToTarget(self, target):
    """move money and coin to comply with target value. target is a dict of {'btce': float, 'stamp': float} denoting
        target bitcoin quantity
        Return False if not enough difference to move
        """

    balance_btce = self.trader.getBalance("btce")
    adjust_btce = target['btce'] - balance_btce['btc']  # >0 : buy
    balance_stamp = self.trader.getBalance("stamp")
    adjust_stamp = target['stamp'] - balance_stamp['btc']
    if abs(adjust_btce) < 0.1 and abs(adjust_stamp) < 0.1:
        return False
    self.log.info("Target:" + str(target) + "adjust_btce " + str(adjust_btce) + " adjust_stamp " + str(adjust_stamp))
    # BTCE
    if adjust_btce > 0.1:  # buy in btce
        amount_buy = round((adjust_btce * self.fee1 - 0.0005), 8)
        if amount_buy > 0:
            print "btce amount buy", amount_buy
            isSuccess = self.trader.trade("btce", "buy", amount_buy, suggested_rate=self.trader.hr_btce.getValue()[3])
            # self.trader.trade("btce", "buy", amount_buy)
            if not isSuccess:
                return False
    elif adjust_btce < -0.1:  # sell in btce
        amount_sell = round((-adjust_btce - 0.0005), 8)
        if amount_sell > 0:
            print "btce amount sell", amount_sell
            isSuccess = self.trader.trade("btce", "sell", amount_sell, suggested_rate=self.trader.hr_btce.getValue()[1])
            # self.trader.trade("btce", "sell", amount_sell)
            if not isSuccess:
                return False
    #STAMP
    if adjust_stamp > 0.1:  # buy in stamp
        amount_buy = round((adjust_stamp * 1 - 0.0005), 8)  # stamp will automatically increase 5% fee
        if amount_buy > 0:
            print "stamp amount buy", amount_buy
            isSuccess = self.trader.trade("stamp", "buy", amount_buy, suggested_rate=self.trader.hr_stamp.getValue()[3])
            # self.trader.trade("stamp", "buy", amount_buy)
            if not isSuccess:
                return False
    elif adjust_stamp < -0.1:
        amount_sell = round((-adjust_stamp - 0.0005), 8)
        if amount_sell > 0:  # sell in stamp
            print "stamp amount sell", amount_sell
            isSuccess = self.trader.trade("stamp", "sell", amount_sell,
                                          suggested_rate=self.trader.hr_stamp.getValue()[1])
            # self.trader.trade("stamp", "sell", amount_sell)
            if not isSuccess:
                return False
    self.isCurrentActionDone = False
    return True


def move(self, amount=0, isLeft=True):
    """move money and coin. Left = buy coin in stamp and sell coin in btce"""
    if isLeft:
        amount_buy = round((amount * 1 - 0.0005), 8)  # stamp will automatically increase 5% fee
        amount_sell = round((amount - 0.0005), 8)
        if amount_buy > 0 and amount_sell > 0:
            print "stamp amount buy", amount_buy
            print "btce amount sell", amount_sell
            self.trader.trade("stamp", "buy", amount_buy, rate=self.trader.hr_stamp.getValue()[3])
            self.trader.trade("btce", "sell", amount_sell, rate=self.trader.hr_btce.getValue()[1])
            self.log.info("Left " + str(amount_buy))
    else:
        amount_buy = round((amount * self.fee1 - 0.0005), 8)
        amount_sell = round((amount - 0.0005), 8)
        if amount_buy > 0 and amount_sell > 0:
            print "btce amount buy", amount_buy
            print "stamp amount sell", amount_sell
            self.trader.trade("btce", "buy", amount_buy, rate=self.trader.hr_btce.getValue()[3])
            self.trader.trade("stamp", "sell", amount_sell, rate=self.trader.hr_stamp.getValue()[1])
            self.log.info("Right " + str(amount_buy))
    self.isCurrentActionDone = False


def initStrategy(self):
    '''Regsiter all strategies to run, priority goes from small to large order'''
    self.strategyList = {}
    arg = self.arg

    self.addStrategy(S_ExchangeDiff('Difference', arg, 10, source1=self.trader.hr_btce, source2=self.trader.hr_stamp))
    self.addStrategy(S_MA('Diff MA', arg, 20, length=3000, source=self.strategyList['Difference']))
    self.strategyList['Difference'].source3 = self.strategyList['Diff MA']

    self.addStrategy(
        D_Trend('Diff Comparer', arg, 30, source1=self.strategyList['Difference'], source2=self.strategyList['Diff MA'],
                threshold=3))

    self.sortedStrategyList = sorted(self.strategyList.iteritems(), key=lambda e: int(e[1].priority))


def addStrategy(self, strategy):
    self.strategyList[strategy.name] = strategy


def updateStrategy(self):
    '''Run every strategy one by one'''
    for strategyname, strategy in self.sortedStrategyList:
        # sys.stdout.write ('Executing ' + strategyname + '\n')
        strategy.update()


def startStrategy(self):
    for strategyname, strategy in self.sortedStrategyList:
        strategy.start()


class Strategy(object):
    def __init__(self, name, arg, priority, **kwds):
        self.name = name
        self.arg = arg
        self.simMode = arg.get('simMode', 1)
        self.config = arg.get('config', None)
        self.breakpoint = arg.get('breakpoint', None)
        self.plot = arg.get('plot', None)

        self.decision = {}
        self.kwds = kwds
        self.priority = priority
        self.data = []
        self.value = (0, 0)
        self.init()

    def init(self):
        '''Overwritten by subclass to acomplish individual initialization'''
        pass

    def update(self):
        '''Overwritten by subclass to acomplish individual update'''
        pass

    def setValue(self, values):
        self.value = (int(values[0]), float(values[1]))
        self.data.append(self.value)
        # if len(self.data) > 0:
        #     self.data[-1] = self.value
        #     # self.plot.update(self.name, self.value)
        # else:
        #     self.data.append(self.value)
        #     # self.plot.append(self.name, self.value)

    def start(self):
        if self.value != None:
            self.data.append(self.value)
            # self.plot.append(self.name, self.value)

    def getValue(self):
        return self.value

    def getData(self):
        return self.data


class S_ExchangeDiff(Strategy):
    def init(self):
        # print self.name, "initializing"
        self.source1 = self.kwds['source1']
        self.source2 = self.kwds['source2']
        self.source3 = None
        self.prepare()

    def prepare(self):
        fullList1 = self.source1.getData()
        fullList2 = self.source2.getData()
        gen2 = (x for x in fullList2)
        try:
            item2 = gen2.next()
            for item1 in fullList1:
                while (item2 is None) or (item2[0] < item1[0]):
                    item2 = gen2.next()
                if abs(item2[0] - item1[0] > 10):  # time difference too large, discard
                    continue
                self.update(item1, item2)
        except Exception, e:
            print "In prepare", e

            # data.append((item1, item2, item1[1] - item2[1]))
            # for i in range(0, len(fullList1)):
            # self.start()
            #     self.update(fullList1[i], fullList2[i])

    def update(self, newPrice1=None, newPrice2=None):
        """
        item = (int[timestamp], float['bid1'][price], float['bid1'][volume], float['ask1'][price], float['ask1'][volume])
        """
        if newPrice1 is None:
            newPrice1 = self.source1.getValue()
        if newPrice2 is None:
            newPrice2 = self.source2.getValue()
        try:
            diff = float((newPrice1[1] - newPrice2[1]))
            newPrice3 = self.source3.getValue()
            if diff > newPrice3[1]:
                diff = float((newPrice1[1] - newPrice2[3]))
            else:
                diff = float((newPrice1[3] - newPrice2[1]))
        except Exception, e:
            print "in getting ma", e
        try:
            self.setValue((int(newPrice1[0]), diff))
            strdate = datetime.fromtimestamp(newPrice1[0]).isoformat(' ')
            print ('Diff add value' + strdate + ', ' + str(self.getValue()[1]))
        except Exception, e:
            print "In update", e


class S_MA(Strategy):
    def init(self):
        self.avgLength = int(self.kwds['length'])
        self.enabled = True
        self.source = self.kwds.get('source', None).getData()
        self.prepare()

    def prepare(self):
        # for i in range(min(0, len(self.source) - 1000), len(self.source)):
        for i in range(0, len(self.source)):
            self.start()
            self.update(i)

    def update(self, index=-1):
        '''If index = -1 then update from realtime value'''
        temp = [self.source[i][1] for i, x in enumerate(self.source)]
        if index >= self.avgLength - 1 or index == -1:
            self.setValue((self.source[index][0], sum(temp[index - self.avgLength:index]) / float(self.avgLength)))
        else:
            self.setValue((self.source[index][0], sum(temp[:index]) / float(index + 1)))
        if index == -1:
            print "MA", self.value
        return self.value


class D_Trend(Strategy):
    def init(self):
        self.source1 = self.kwds['source1']
        self.source2 = self.kwds['source2']

        self.threshold = float(self.kwds.get('threshold', 0))
        self.lastDecision = {}

    def update(self):
        value = self.source1.getValue()[1]
        ma_value = self.source2.getValue()[1]
        timestamp = self.source1.getValue()[0]
        strdate = datetime.fromtimestamp(timestamp).isoformat(' ')
        # print strdate, value
        if value - ma_value > self.threshold:
            self.decision = {'action': 'left', 'vol': 1.0, 'value': value}
            print strdate, self.decision
        elif value - ma_value < -self.threshold:
            self.decision = {'action': 'right', 'vol': 1.0, 'value': value}
            print strdate, self.decision
        else:
            self.decision = {}

        if self.decision == self.lastDecision:  # if there is no change made on decision, clear decision
            self.decision = {}
        else:
            self.lastDecision = self.decision  # backup

    def start(self):
        pass