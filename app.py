import helper
import logging
import os
import manager


def setLog(simMode):
    if simMode == 0:  # external import data
        filename_ = 'simlog_ext.txt'
    elif simMode == 1:  # realtime simulating
        filename_ = 'simlog.txt'
    else:  # trading
        filename_ = 'log.txt'
    format_ = '%(asctime)s %(name)s %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format=format_,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=filename_
    )
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter(format_, datefmt='%Y-%m-%d %H:%M:%S')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logging.getLogger("requests").setLevel(logging.WARNING)


'''Main'''
os.system('cls')
print "BTC arbitrage bot starting"
simMode = 2  # 0 for external import data, 1 for real time tracking without trading, 2 for trading
setLog(simMode)
config = helper.Config()
arg = {"simMode": simMode, "config": config}
botmanager = manager.Manager(arg)
if simMode == 0:
    botmanager.runLoopSim()
else:
    # botmanager.runOnce()
    botmanager.runLoop()