import suds
import xmltodict
from json import loads, dumps
from collections import OrderedDict
from tinydb import TinyDB, where
import time
import shutil
import whoosh.index as windex
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.query import *
import urllib2
import base64
import json
import re
from itertools import islice

dbSicris = TinyDB('/home/luis/data/mario/openedu/tinydb/sicris.json')
dbVideoLectures = TinyDB('/home/luis/data/mario/openedu/tinydb/videolectures.json')
dbNets = TinyDB('/home/luis/data/mario/openedu/tinydb/nets.json')
dbSicrisConn = TinyDB('/home/luis/data/mario/openedu/tinydb/conn.json')
tblRsr = dbSicris.table("rsr")
tblPrj = dbSicris.table("prj")
tblOrg = dbSicris.table("org")
tblLec = dbVideoLectures.table("lec")
tblRsrPrj = dbSicrisConn.table("rsr_prj")
tblRsrColl = dbNets.table("rsr_colls")
tblRsrPrjColl = dbNets.table("rsr_prj_coll_net")
tblRsrPrjCollW = dbNets.table("rsr_prj_coll_net_w")


