from flask import Flask
from data import get_data
import json
import time
import pprint

path = "/home/luis/data/mario/openedu/"
t1 = time.time()
print "Start session... " + str(t1)
get_data.getAllSIO()
t2 = time.time()
