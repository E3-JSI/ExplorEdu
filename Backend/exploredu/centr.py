from flask import Flask
from data import get_data
from data import graphs
import json
import time
import pprint

# Start session
t1 = time.time()
print "Start session... " + str(t1)
graphs.gcentrality()
t2 = time.time()
print (t2 - t1)/(60*60)
