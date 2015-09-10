import time
import logging
from datetime import datetime
import sys
import trader
import pandas as pd
import pickle
import random
import math
from sklearn.linear_model import LogisticRegression


class Manager(object):
    def __init__(self, arg):
        self.arg = arg
        self.simMode = arg.get('simMode', 1)
        self.config = arg.get('config', None)
        self.plot = arg.get('plot', None)

        self.fee1 = 1.002
        self.fee2 = 1.0024

        self.moveAmount = 8.0
        self.moveStep = 2.0
        self.moveAmountPosition = 0

        self.log = logging.getLogger('manager')
        self.loadTradeModel()

        self.isCurrentActionDone = True
        self.currentDecision = {}

        self.trader = trader.trader(arg)
        self.initStrategy()

    # def runOnce(self):
    # amount = self.getMoveAmount(False)
    #     self.move(amount, False)

    def loadTradeModel(self):
        try:
            self.tradeModel = pickle.load(open(self.config.modelfile, 'rb'))
            print self.config.modelfile, "loaded."
        except Exception, e:
            print "In load trade model", e

    def runLoop(self):
        interval = 10  # 10s for real trading
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
                    val = (self.strategyList['Difference'].getData().iloc[-1])['diff']
                    self.log.info(self.currentDecision.get('action', 'None') + " at " + str(val) + str(
                        self.trader.getBalance("all")) + " btce " + str(
                        self.trader.getBalance("btce")) + " stamp " + str(self.trader.getBalance("stamp")))
                    self.updateMoveAmountPosition()
                    self.strategyList['MinThresholdFilter'].updateLastTrade(self.currentDecision.get('action', 'None'), val)
                else:  # if not, kill them
                    self.trader.killAll("btce")
                    self.trader.killAll("stamp")
                    time.sleep(5)

                    self.makeDecision(self.currentDecision)  #TODO: smarter control of resubmit decision

            if self.isCurrentActionDone:
                self.currentDecision = self.strategyList["MinThresholdFilter"].decision
                self.makeDecision(self.currentDecision)
            timer = time.time()
            # sys.stdout.write(".")
            time.sleep(interval)

            if timer >= nextTriggerTime:
                nextTriggerTime += 15 * interval
                sys.stdout.write(",")
                self.trader.hr_btce.save()
                self.trader.hr_stamp.save()


    def runLoopSim(self):
        pass
        # self.trader.hr_btce.start()
        # self.trader.hr_stamp.start()
        # self.initStrategy()
        # while True:
        #     isRunning = self.trader.hr_btce.start() and self.trader.hr_stamp.start()
        #     if not isRunning:
        #         break
        #     # print self.hr.getValue()
        #     self.updateStrategy()
        #     self.currentDecision = self.strategyList["Diff Comparer"].decision
        #     self.makeDecision(self.currentDecision)
        #     # self.startStrategy()


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

    def updateMoveAmountPosition(self):
        """return the current position of amount of coins available for moving, after fee, in terms of btce coin amount"""
        balance_btce = self.trader.getBalance("btce")
        balance_stamp = self.trader.getBalance("stamp")
        pos = float(balance_btce['btc']) - 0.1
        pos_stamp = self.moveAmount - (float(balance_stamp['btc']) - 0.1)
        pos = min(pos, pos_stamp)
        # print "Pos", "%.2f" % pos
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
                if not isSuccess:
                    return False
        elif adjust_btce < -0.1:  # sell in btce
            amount_sell = round((-adjust_btce - 0.0005), 8)
            if amount_sell > 0:
                print "btce amount sell", amount_sell
                isSuccess = self.trader.trade("btce", "sell", amount_sell, suggested_rate=self.trader.hr_btce.getValue()[1])
                if not isSuccess:
                    return False
        #STAMP
        if adjust_stamp > 0.1:  # buy in stamp
            amount_buy = round((adjust_stamp * 1 - 0.0005), 8)  # stamp will automatically increase 5% fee
            if amount_buy > 0:
                print "stamp amount buy", amount_buy
                isSuccess = self.trader.trade("stamp", "buy", amount_buy, suggested_rate=self.trader.hr_stamp.getValue()[3])
                if not isSuccess:
                    return False
        elif adjust_stamp < -0.1:
            amount_sell = round((-adjust_stamp - 0.0005), 8)
            if amount_sell > 0:  # sell in stamp
                print "stamp amount sell", amount_sell
                isSuccess = self.trader.trade("stamp", "sell", amount_sell,
                                              suggested_rate=self.trader.hr_stamp.getValue()[1])
                if not isSuccess:
                    return False
        self.isCurrentActionDone = False
        return True

    def initStrategy(self):
        '''Regsiter all strategies to run, priority goes from small to large order'''
        self.strategyList = {}
        arg = self.arg

        self.addStrategy(S_ExchangeDiff('Difference', arg, 10, source1=self.trader.hr_btce, source2=self.trader.hr_stamp))
        self.addStrategy(S_FeatureGenerator('FeatureGenerator', arg, 20, source=self.strategyList['Difference']))
        self.addStrategy(D_Predictor('BurgerKing', arg, 30, source=self.strategyList['FeatureGenerator'], model=self.tradeModel))
        self.addStrategy(D_Filter('MinThresholdFilter', arg, 40, source=self.strategyList['BurgerKing'], source_diff=self.strategyList['Difference']))

        ################################################################################################
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
        self.meanWindow = 100
        self.source1 = self.kwds['source1']
        self.source2 = self.kwds['source2']
        self.data = []
        self.cols = ['timestamp', 'Lbid', 'Lask', 'Rbid', 'Rask', 'diff1', 'diff2', 'mean', 'diff']
        self.df = pd.DataFrame()
        self.prepare()

    def prepare(self):
        fullList1 = self.source1.getData()
        fullList2 = self.source2.getData()
        gen2 = (x for x in fullList2)
        try:
            item2 = gen2.next()
            for item1 in fullList1:
                if not item1 is None:
                    while (item2 is None) or (item2[0] < item1[0]):
                        item2 = gen2.next()
                    if abs(item2[0] - item1[0] > 10):  # time difference too large, discard
                        continue
                    self.data.append([item1[0], item1[1], item1[3], item2[1], item2[3]])
        except Exception, e:
            print "In prepare of ExchangeDiff", e
        self.df = pd.DataFrame(self.data, columns=self.cols[:5])
        self.df['diff1'] = self.df.Lbid - self.df.Rask
        self.df['diff2'] = self.df.Lask - self.df.Rbid
        self.df['mean'] = pd.rolling_mean(self.df['diff1'], self.meanWindow, min_periods=1)
        self.df['diff'] = self.df.apply(lambda x: x.diff1 if x.diff1 > x.mean else x.diff2, axis=1)


    def update(self):
        """
        item = (int[timestamp], float['bid1'][price], float['bid1'][volume], float['ask1'][price], float['ask1'][volume])
        """
        item1 = self.source1.getValue()
        item2 = self.source2.getValue()
        try:
            diff = float((item1[1] - item2[1]))
            mean = (self.df.iloc[-1])['mean']
            if diff > mean:
                diff = float((item1[1] - item2[3]))
            else:
                diff = float((item1[3] - item2[1]))
        except Exception, e:
            print "In getting MA for ExchangeDiff", e
        try:
            mean = (self.df[-self.meanWindow:])['diff'].mean()
            self.df = self.df.append(pd.Series([item1[0], item1[1], item1[3], item2[1], item2[3], float((item1[1] - item2[3])), float((item1[3] - item2[1])), mean, diff],
                                               index=self.cols), ignore_index=True)
            strdate = datetime.fromtimestamp(item1[0]).isoformat(' ')
            print ('Difference add ' + strdate + ', ' + str(diff))
        except Exception, e:
            print "In update of ExchangeDiff", e

    def getData(self):
        return self.df[['timestamp', 'diff']]


class S_FeatureGenerator(Strategy):
    def init(self):
        self.source = self.kwds.get('source', None).getData()
        self.data = None

    def prepare(self):
        """create all features here"""
        df = self.source.iloc[-3000:].copy()
        windows = [40, 100, 200, 300, 500, 1000, 2000, 3000]
        for window in windows:
            lengthname = str(window)
            df['mean'+lengthname] = pd.rolling_mean(df['diff'], window)
            df['var'+lengthname] = pd.rolling_var(df['diff'], window)
        df = df.dropna()
        self.data = df

    def update(self):
        self.source = self.kwds.get('source', None).getData()
        self.prepare()

    def getFeatures(self):
        """return a numpy row of features"""
        return self.data.iloc[-1].drop('timestamp').as_matrix()

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


class D_Predictor(Strategy):
    def init(self):
        self.source = self.kwds.get('source', None)
        self.features = None
        self.model = self.kwds.get('model', None)
        self.decision = {}

    def update(self):
        self.features = self.source.getFeatures()
        self.decision = self.predict()

    def predict(self):
        '''return decision made from the model'''
        predicted = (self.model.predict(self.features))[0]
        prob = self.model.predict_proba(self.features)[0]*100
        # workaround, need retrain the model
        # if prob[0] > 49:
        #     predicted = -1
        # if prob[2] > 49:
        #     predicted = 1
        print "L/Sell", "%.2f" % prob[0], "%,", "R/Buy", "%.2f" % prob[2], "%"
        decision = {}
        if predicted == -1:
            decision = {'action': 'left'}
            print decision
        elif predicted == 1:
            decision = {'action': 'right'}
            print decision
        return decision

class D_Filter(Strategy):
    def init(self):
        self.source = self.kwds['source']
        self.source_diff = self.kwds['source_diff']
        self.lastTrade = {}
        self.loadBreakpoint()
        self.multiplier = 0.5
        self.minThreshold = 3
        self.decision = {}

    def loadBreakpoint(self):
        try:
            self.lastTrade = pickle.load(open('LastTrade', 'rb'))
            print 'Last trade loaded', self.lastTrade
        except Exception, e:
            print 'In load breakpoint', e
            self.lastTrade = {'left': -4, 'right': -5}

    def updateLastTrade(self, direction, val):
        if direction == "left" or direction == "right":
            self.lastTrade[direction] = val
            self.saveBreakpoint()
        else:
            print "Direction wrong"

    def saveBreakpoint(self):
        pickle.dump(self.lastTrade, open('LastTrade', 'wb'))

    def update(self):
        self.decision = self.source.decision
        if self.decision != {}:
            val = (self.source_diff.getData().iloc[-1])['diff']
            action = self.decision.get('action', None)
            if action == 'left': # sell
                delta = val - self.lastTrade['right']
            elif action == 'right':
                delta = -val + self.lastTrade['left']
            else:
                delta = 0
                print "Error in getting action"
            if random.random() < math.exp(self.multiplier*(self.minThreshold-delta)):
                print "Price Delta", delta, "Decision abandoned"
                self.decision = {}





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