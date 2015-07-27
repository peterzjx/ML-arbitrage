import logging
import time
from ConfigParser import SafeConfigParser
import pylab


class Config(object):
    '''Read a user configuration file, store values in instance variables'''

    def __init__(self, f='settings.ini'):
        self.file = f
        self.parser = SafeConfigParser()
        self.updateAll()

    def updateAll(self):
        '''Update and store all user settings'''
        self.parser.read(self.file)  # TODO: except if file not found, generate defaults
        # API Info
        self.apikey_btce = self.parser.get('BTCE', 'key')
        self.apisecret_btce = self.parser.get('BTCE', 'secret')

        self.apikey_stamp = self.parser.get('Stamp', 'key')
        self.apisecret_stamp = self.parser.get('Stamp', 'secret')
        self.apiid_stamp = self.parser.get('Stamp', 'id')
        # Settings
        self.savefile_btce = self.parser.get('Settings', 'savefile_1')
        self.savefile_stamp = self.parser.get('Settings', 'savefile_2')

        # Trading
        self.pair = 'btc_usd'
        self.simMode = self.parser.getint('Trading', 'simMode')


class Breakpoint(object):
    '''Store breakpoint data for recovery'''

    def __init__(self, simMode):

        pass
    # if simMode == 2:
    # f = 'breakpoint.ini'
    # else:
    # 	f = 'simbreakpoint.ini'
    # self.log = logging.getLogger('Breakpoint')
    # self.file = f
    # self.parser = SafeConfigParser()
    # self.updateAll()

    def updateAll(self):

        pass

# try:
# 		self.parser.read(self.file)
# 	except TypeError, e:
# 		self.log.critical("Breakpoint file error" + str(e))
# 	self.avgCost = self.parser.get('Stoploss', 'avgCost')
# 	self.highest = self.parser.get('Stoploss', 'highest')
# 	self.lowest = self.parser.get('Stoploss', 'lowest')
# 	self.log.info("Breakpoint file OK")
#
#
# def setValue(self, section, option, value):
# 	self.parser.set(section, option, value)
# 	with open(self.file, 'wb') as configfile:
# 		self.parser.write(configfile)
#
# def writeBreakpoint(self, arg):
# 	for (section, option, value) in arg:
# 		self.parser.set(str(section), str(option), str(value))
# 	with open(self.file, 'wb') as configfile:
# 		self.parser.write(configfile)

# Python is awesome
