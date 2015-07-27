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

        # Model
        self.modelfile = self.parser.get('Model', 'model')

        # Trading
        self.pair = 'btc_usd'
        self.simMode = self.parser.getint('Trading', 'simMode')