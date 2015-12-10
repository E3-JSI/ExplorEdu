from flask import Flask
from data import get_data
import json
import time

t1 = time.time()
client = get_data.createClient()
sessionId = get_data.getSessionId(client)
'''
#get_data.getAllRsr(client, sessionId)
t2 = time.time()
print t2 - t1
#get_data.getAllRsrKeyws(client, sessionId, get_data.tblRsr,"slv")
t3 = time.time()
print t3 - t2
index = get_data.createIndexRsr(get_data.tblRsr)
get_data.getAllPrj(client, sessionId, "eng")
t4 = time.time()
print (t4 - t1)/(60*60)
get_data.getAllPrjDetails(client, sessionId, "eng", get_data.tblPrj)
t5 = time.time()
print (t5 - t1)/(60*60)
get_data.getAllOrgDetails(client, sessionId, "eng", get_data.tblOrg)
t6 = time.time()
print (t6 - t1)/(60*60)
client_vl = get_data.createClientVideoLectures()
get_data.getAllVideoLectures(client_vl)
t7 = time.time()
print (t7 - t1)/(60*60)
'''
get_data.createRsrPrjCollNet()
t8 = time.time()
print (t8 - t1)/(60*60)
get_data.createRsrPrjCollNetWeighted()
t9 = time.time()
print (t9 - t1)/(60*60)
