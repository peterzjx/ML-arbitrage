__author__ = 'Peter'
import trader
import helper
import time
import manager

simMode = 2
config = helper.Config()
breakpoint = helper.Breakpoint(simMode)
arg = {"simMode": simMode, "config": config, "breakpoint": breakpoint}
mng = manager.Manager(arg)
mng.move(0, True)