from flask import Flask
from data import get_data
import json
import time

t1 = time.time()
print "tblRsr", len(get_data.tblRsr.all())
print "tblPrj", len(get_data.tblPrj.all())
print "tblOrg", len(get_data.tblOrg.all())
print "tblLec", len(get_data.tblLec.all())
print "tblRsrPrj", len(get_data.tblRsrPrj.all())
print "tblRsrPrjColl", len(get_data.tblRsrPrjColl.all())
print "tblRsrPrjCollW", len(get_data.tblRsrPrjCollW.all())
t2 = time.time()
print "time", (t2 - t2)/(60*60)
