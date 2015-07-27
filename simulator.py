import sys
import pickle
import logging


class simulator(object):
    def __init__(self, exchange, initAsset, arg, hr, fee):
        self.exchange = exchange
        self.usd = initAsset["usd"]
        self.btc = initAsset["btc"]

        self.arg = arg
        self.simMode = arg.get('simMode', 1)
        self.config = arg.get('config', None)
        self.breakpoint = arg.get('breakpoint', None)
        self.plot = arg.get('plot', None)

        self.hr = hr
        self.fee = fee
        # self.plot.addLine('Buy', shape='bar', color='r')
        # self.plot.addLine('Sell', shape='bar', color='g')
    def buy(self, rate, amount, seconds = 0):
        maxAmount = self.usd / rate
        amount = min(amount, maxAmount)
        # self.log.info('SimBuy @' + str(rate) + ' vol:' + str(amount))
        print ('SimBuy @' + str(rate) + ' vol:' + str(amount))
        self.usd -= rate * amount
        self.btc += amount * (1 - self.fee)
        timeStamp = float(self.hr.getValue()[0])
        # self.log.info('usd:' + str(self.usd) + ' btc:' + str(self.btc) + ' tot:' + str(self.calcAsset(rate)))
        print (self.exchange + 'usd:' + str(self.usd) + ' btc:' + str(self.btc) + ' tot:' + str(self.calcAsset(rate)))
        # self.plot.append('Buy', (timeStamp, rate))

    def sell(self, rate, amount, seconds = 0):
        maxAmount = self.btc
        amount = min(amount, maxAmount)
        #  self.log.info('SimSell @' + str(rate) + ' vol:' + str(amount))
        print ('SimSell @' + str(rate) + ' vol:' + str(amount))
        self.btc -= amount
        self.usd += rate * amount * (1 - self.fee)
        timeStamp = float(self.hr.getValue()[0])
        # self.log.info('usd:' + str(self.usd) + ' btc:' + str(self.btc) + ' tot:' + str(self.calcAsset(rate)))
        print (self.exchange + 'usd:' + str(self.usd) + ' btc:' + str(self.btc) + ' tot:' + str(self.calcAsset(rate)))
        # self.plot.append('Sell', (timeStamp, rate))

    def calcAsset(self, rate):
        return self.usd + self.btc * rate


class simHistoryRecorder(object):
    def __init__(self, arg, exchange):
        self.arg = arg
        self.simMode = arg.get('simMode', 1)
        self.config = arg.get('config', None)
        self.breakpoint = arg.get('breakpoint', None)
        # self.plot = arg.get('plot', None)

        self.exchange = exchange
        self.data = []
        self.history = []

        if self.exchange == "btce":
            self.savefile = self.config.savefile_btce
        elif self.exchange == "stamp":
            self.savefile = self.config.savefile_stamp
        self.newSingleGenerator = self.yieldNewSingle()

        self.load()
        # for item in self.data:
        #     self.plot.append('Single', (item[0], item[4]))

    def cut(self, start, end):
        self.history = self.history[start:end]
        self.newSingleGenerator = self.yieldNewSingle()

    def load(self):
        try:
            f = open(self.savefile, 'rb')
            self.history = pickle.load(f)
            print "Current length of data depth", self.savefile, len(self.history)
            f.close()
        except (IOError, TypeError, EOFError), e:
            print 'Load price info error'
            print e

    def yieldNewSingle(self):
        for item in self.history:
            # for item in reversed(self.history):
            yield item

    def start(self):
        try:
            newData = self.newSingleGenerator.next()
        # print newData
        except Exception, e:
            print e
            return False
        self.data.append(newData)
        # self.plot.append('Single', (newData[0], newData[4]))
        return True

    def getData(self):
        return self.data

    def getValue(self):
        return self.data[-1]