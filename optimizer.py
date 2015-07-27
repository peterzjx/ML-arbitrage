__author__ = 'Peter'
import pickle
import matplotlib.pyplot as plt
import numpy as np

class Optimizer(object):
    def __init__(self):
        self.data_btce = []
        self.data_stamp = []

    def load(self):
        try:
            f = open('dev/btce.depth', 'rb')
            self.data_btce = pickle.load(f)
            print self.data_btce[-1]
            print "Current length of data depth", len(self.data_btce)
            f.close()
        except (IOError, TypeError, EOFError), e:
            print 'Load price info error'
            print e

        try:
            f = open('dev/stamp.depth', 'rb')
            self.data_stamp = pickle.load(f)
            print self.data_stamp[-1]
            print "Current length of data depth", len(self.data_stamp)
            f.close()
        except (IOError, TypeError, EOFError), e:
            print 'Load price info error'
            print e

    def plot(self):
        data = []
        t = []
        fullList1 = self.data_btce
        fullList2 =self.data_stamp
        gen2 = (x for x in fullList2)
        try:
            item2 = gen2.next()
            for item1 in fullList1:
                while (item2 is None) or (item2[0] < item1[0]):
                    item2 = gen2.next()
                if abs(item2[0] - item1[0] > 10):  # time difference too large, discard
                    continue
                t.append(item1[0])

                diff = float((item1[1] - item2[1]))
                if diff > -1:
                    diff = float((item1[1] - item2[3]))
                else:
                    diff = float((item1[3] - item2[1]))
                data.append(diff)
        except Exception, e:
            print "In prepare", e
        ma = []
        for i, p in enumerate(data):
            width = 2000
            avg = float(sum(data[max(i-width/2, 0):min(i+width/2,len(data))]))/width
            ma.append(avg)
        plt.plot(t, data)
        plt.plot(t, ma)
        plt.show()

op = Optimizer()
op.load()
op.plot()
