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
from whoosh.qparser import MultifieldParser
from whoosh.query import *
import urllib2
import base64
import json
import re
from itertools import islice
from random import randint
from EventRegistry.EventRegistry import *
from lxml import html
import requests
import 	rdflib
import codecs
#import wikipedia

# Set main data path
path = "/home/luis/data/mario/openedu/"

# Databases
dbSicris = TinyDB(path+'tinydb/sicris.json')
dbVideoLectures = TinyDB(path+'tinydb/videolectures.json')
dbNets = TinyDB(path+'tinydb/nets.json')
dbSicrisConn = TinyDB(path+'tinydb/conn.json')
dbCach = TinyDB(path+'tinydb/cach.json')
dbER = TinyDB(path+'tinydb/er.json')
dbSio = TinyDB(path+'tinydb/sio.json')
dbZakoni = TinyDB(path+'tinydb/zakoni.json')

# Tables
# --- sicris
tblRsr = dbSicris.table("rsr")
tblPrj = dbSicris.table("prj")
tblOrg = dbSicris.table("org")
# --- lec
tblLec = dbVideoLectures.table("lec")
# --- conn
tblRsrPrj = dbSicrisConn.table("rsr_prj")
# --- nets
earblRsrColl = dbNets.table("rsr_colls")
tblRsrPrjColl = dbNets.table("rsr_prj_coll_net")
tblRsrPrjCollW = dbNets.table("rsr_prj_coll_net_w")
# --- cache
tblRsrPrjGraphCache = dbCach.table("rsr_prj_graph")
# --- events
tblEvents = dbER.table("events")
# --- sio educational materials
tblEduMaterials = dbSio.table("materials")
tblOds = dbSio.table("ods")
# --- zakoni
tblZakoni = dbZakoni.table("zakoni")
# --- oer
tblOer = dbSio.table("oer")


# from sorted dict to dict
def to_dict(input_ordered_dict):
    return loads(dumps(input_ordered_dict))

##################
# Data connections
##################

# create client for sicris
def createClientSicris():
    url = "http://webservice.izum.si/ws-cris/CrisService.asmx?WSDL"
    return suds.client.Client(url)

# create client for videolectures
def createClientVideoLectures(username, password):
    url = "http://videolectures.net/site/stats/lectures.json"
    request = urllib2.Request(url)
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)   
    return request

def getSessionId(client, username, password):
    return client.service.GetSessionID("si", username, password)

###################
# Data collection
###################

# Get list of researchers from SICRIS   
def getAllRsr(client, path, sessionId):
    shutil.copyfile(path+'tinydb/sicris.json', path+'tinydb/sicris.json.backup')
    methodCall = "Sicris_app_UI.Researcher.SearchSimple.eng.public.utf-8.mstid.%.1.-1"
    tblRsr.purge()
    result = client.service.Retrieve("si", "RSR", methodCall, "", sessionId)
    res = result.Records
    obj = xmltodict.parse(res)
    for rsr in obj['CRIS_RECORDS']['RSR']:
        tblRsr.insert(to_dict(rsr))

def searchAllZakoni():
    res = tblZakoni.all()
    return res[::-1]

def searchNumZakoni(num):
    res = tblZakoni.all()
    res = res[::-1]
    if int(num) <= len(res):
        res = res[0:int(num)]
    return res

# Get keywords of researchers
def getAllRsrKeyws(client, path, sessionId, lang, rsrs):
    shutil.copyfile(path+'tinydb/sicris.json', path+'tinydb/sicris.json.backup')
    methodCall = "Sicris_app_UI.Researcher.GetKeywords."+lang+"."
    for rsr in rsrs.all():
        result = client.service.Retrieve("SI", "RSR", methodCall+rsr["@id"], "", sessionId)
        res = result.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass
        
        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
                # get od record
                old = tblRsr.get(where('@id') == rsr["@id"])
                # update it
                old['keyws_'+lang[0:2]] = rec['RSR']
                # overwrite it
                tblRsr.update(old, where('@id') == rsr["@id"])

# Get classification for researchers
def getAllRsrClass(client, sessionId, lang, rsrs):
    methodCall = "Sicris_app_UI.Researcher.GetMSTClassification."+lang+"."
    for rsr in rsrs.all():
        results = client.service.Retrieve("SI", "RSR", methodCall+rsr["@id"], "", sessionId)
        res = result.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass

        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
                # get od record
                old = tblRsr.get(where('@id') == rsr["@id"])
                # update it
                old['class_'+lang[0:2]] = rec['RSR']
                # overwrite it
                tblRsr.update(old, where('@id') == rsr["@id"])

# Get projects of researchers
def getAllRsrPrj(client, path, sessionId, lang, prjs):
    methodCall = "Sicris_app_UI.Project.GetResearchers."+lang+"."
    shutil.copyfile(path+'tinydb/sicris.json', path+'tinydb/sicris.json.backup')
    tblRsrPrj.purge()
    totallen = len(prjs.all())
    #print totallen
    for i,prj in enumerate(prjs.all()):
        prjid = prj["@id"]
        results = client.service.Retrieve("SI", "RSR", methodCall+prj["@id"]+".RSR", "mstid", sessionId)
        res = results.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass

        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
                # get od record
                rsrs = rec['RSR']
                for rsr in rsrs:
                    #if isinstance(rsr, dict):
                    tblRsrPrj.insert({'prjid': prjid, 'rsrmstid': rsr['@mstid'] })
        #print i, totallen

# Get projects of researchers
def getAllPrjRsr(client, path, sessionId, lang, rsrs):
    methodCall = "Sicris_app_UI.Researcher.GetProjects.PRJ."+lang+"."
    shutil.copyfile(path+'tinydb/sicris.json', path+'tinydb/sicris.json.backup')
    tblRsrPrj.purge()
    totallen = len(rsrs.all())
    #print totallen
    for i,rsr in enumerate(rsrs.all()):
        rsrid = rsr["@id"]
        call = methodCall+rsr["@id"]
        #print call
        results = client.service.Retrieve("SI", "PRJ", call,"", sessionId)
        res = results.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass

        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
                # get od record
                prjs = rec['PRJ']
                for prj in prjs:
                    if isinstance(prj, dict):
                        if (prj.has_key('@mstid')):
                            #print {'prjmstid': prj['@mstid'], 'rsrid': rsrid, 'prjid:':prj['@id']}
                            tblRsrPrj.insert({'prjmstid': prj['@mstid'], 'prjid:':prj['@id'], 'rsrid': rsrid })
        #print i, totallen

# Get all sicris projects
def getAllPrj(client, path, sessionId, lang):
    shutil.copyfile(path+'tinydb/sicris.json', path+'tinydb/sicris.json.backup')
    #tblPrj.purge()
    methodCall = "Sicris_app_UI.Project.SearchSimple.PRJ."+lang+".public.utf-8.mstid.%.1.-1"
    results = client.service.Retrieve("SI", "PRJ", methodCall, "", sessionId)
    res = results.Records
    obj = {}

    try:
        obj = xmltodict.parse(res)
        obj = to_dict(obj)
    except:
        pass

    for i,prj in enumerate(obj['CRIS_RECORDS']['PRJ']):
        #print i,len(obj['CRIS_RECORDS']['PRJ'])
        tblPrj.insert(to_dict(prj))

# Gett project abstract and keywords
def getAllPrjDetails(client, path, sessionId, lang, prjs):
    shutil.copyfile(path+'tinydb/sicris.json', path+'tinydb/sicris.json.backup')
    methodCallKeyws = "Sicris_app_UI.Project.GetKeywords."+lang+"."
    methodCallAbst = "Sicris_app_UI.Project.GetAbstract."+lang+"."
    methodCallSign = "Sicris_app_UI.Project.GetSignificance."+lang+"."

    for i,prj in enumerate(prjs.all()):

        # Keywords
        results = client.service.Retrieve("SI", "PRJ", methodCallKeyws+prj["@id"], "", sessionId)
        res = results.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass
       
        keyws = {}
        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
                if rec['PRJ']['@keyws']:
                    keyws = rec['PRJ']['@keyws']
        
        # Abstract
        results = client.service.Retrieve("SI", "PRJ", methodCallAbst+prj["@id"], "", sessionId)
        res = results.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass

        abst = {}
        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
                # get od record
                if rec['PRJ'].has_key('@abstr'):
                    abst = rec['PRJ']['@abstr']
         
        # Significance
        results = client.service.Retrieve("SI", "PRJ", methodCallSign+prj["@id"], "", sessionId)
        res = results.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass
        
        sign_dom = {}
        sign_world = {}
        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
                if rec['PRJ'].has_key('@domestic'):
                    sign_dom = rec['PRJ']['@domestic']
                if rec['PRJ'].has_key('@world'):
                    sign_world = rec['PRJ']['@world']

        # get od record
        old = tblPrj.get(where('@id') == prj["@id"])

        # update it
        if (bool(keyws)):
            old['keyws_'+lang[0:2]] = keyws
        if (bool(abst)):
            old['abstr_'+lang[0:2]] = abst
        if (bool(sign_dom)):
            old['sign_dom_'+lang[0:2]] = sign_dom
        if (bool(sign_world)):
            old['sign_world_'+lang[0:2]] = sign_world
      
        # overwrite it
        if bool(keyws) or bool(abst) or bool(sign_dom) or bool(sign_world):
            tblPrj.update(old, where('@id') == prj["@id"])
        
        #print i

# Get all organization using IZUM webcris service and store it into tblOrg table of sicris tinydb database
def getAllOrg(client, path, sessionId, lang):
    shutil.copyfile(path+'tinydb/sicris.json', path+'tinydb/sicris.json.backup')
    methodCall = "Sicris_app_UI.Organization.SearchSimple.@"+lang+".public.utf-8.mstid.%.1.-1"
    results = client.service.Retrieve("SI", "ORG", methodCall, "", sessionId)
    res = results.Records
    obj = {}

    try:
        obj = xmltodict.parse(res)
        obj = to_dict(obj)
    except:
        pass

    for i,org in enumerate(obj['CRIS_RECORDS']['ORG']):
        #print i,len(obj['CRIS_RECORDS']['ORG'])
        tblOrg.insert(to_dict(org))

# Get details of organizatipon using IZUM webcris service. Use the existing list of organizations from tblOrg table
# of sicris tinydb database
def getAllOrgDetails(client, path, sessionId, lang, orgs):
    shutil.copyfile(path+'tinydb/sicris.json', path+'tinydb/sicris.json.backup')
    methodCallStatus = "Sicris_app_UI.Organization.GetHeader."+lang+"."
    methodCallClass = "Sicris_app_UI.Organization.GetMSTClassification."+lang+"."

    for i,org in enumerate(orgs.all()):

        # Status
        results = client.service.Retrieve("SI", "ORG", methodCallStatus+org["@id"], "", sessionId)
        res = results.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass

        stat = {}
        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
               stat = rec['ORG']
        
        # Classification
        results = client.service.Retrieve("SI", "ORG", methodCallClass+org["@id"], "", sessionId)
        res = results.Records
        obj = {}

        try:
            obj = xmltodict.parse(res)
            obj = to_dict(obj)
        except:
            pass
        
        classi = {}
        if obj.has_key('CRIS_RECORDS'):
            rec = obj['CRIS_RECORDS']
            if rec != None:
               classi = rec['ORG']

        # get od record
        old = tblOrg.get(where('@id') == org["@id"])
        
        # update
        if stat.has_key('@org_name'):
            old['name'] = stat['@org_name']
        if stat.has_key('@statfrm'):
            old['statfrm'] = stat['@statfrm']
        if stat.has_key('@status'):
            old['status'] = stat['@status']
        if stat.has_key('@regnum'):
            old['regnum'] = stat['@regnum'] 
        if bool(classi):
            old['classification'] = classi
        # overwrite
        tblOrg.update(old, where('@id') == org["@id"])
        #print i

# get all videolecturs
def getAllVideoLectures(client, path):
    shutil.copyfile(path+'tinydb/videolectures.json', path+'tinydb/videolectures.json.backup')
    result = urllib2.urlopen(client)
    lectures = json.loads(result.read())
    length = len(lectures)
    for i,l in enumerate(lectures):
        tblLec.insert(lectures[l])
        #if i%10000 == 0:
        #    print i

# get event registry events with concept Education
def getAllEREducationEvents(path):
    er = EventRegistry(host = "http://eventregistry.org", logging = True)
    q = QueryEvents()
    q.addConcept(er.getConceptUri("Education"))
    q.addRequestedResult(RequestEventsUriList())
    res = er.execQuery(q)
    obj = createStructFromDict(res)
    uris = obj.uriList

    l = len(uris)
    inserts = []
    tblEvents.purge()
    for i,uri in enumerate(uris):
        try:
            q = QueryEvent(uri)
            q.addRequestedResult(RequestEventInfo(["eng"]))   # get event information. concept labels should be in three langauges
            q.addRequestedResult(RequestEventArticles(0, 10))   # get 10 articles describing the event
            q.addRequestedResult(RequestEventKeywordAggr())     # get top keywords describing the event
            eventRes = er.execQuery(q)
            out = {}
            out['info'] =  eventRes[uri][u'info'][u'multiLingInfo']
            out['date'] =  eventRes[uri][u'info'][u'eventDate']
            out['uri'] = uri
            tblEvents.insert(out)
            #print i,l
        except:
            pass

def getERNews():
    # Loading credentials
    pwd = {}
    with open('pwd.json') as data_file:
        pwd = json.load(data_file)
    er = EventRegistry()
    er.login(pwd['er']['user'], pwd['er']['pass'])

    q = QueryArticles()     # we want to make a search for articles
    q.addKeyword("education")       # article should contain word apple
    q.addRequestedResult(RequestArticlesInfo(page=0, count = 10));  # get 30 articles that match the criteria
    res = er.execQuery(q)
    return res

def getERNewsRelated(text):
    er = EventRegistry()

    pwd = {}
    with open('pwd.json') as data_file:
        pwd = json.load(data_file)
    er = EventRegistry()
    er.login(pwd['er']['user'], pwd['er']['pass'])

    q = QueryArticles()     # we want to make a search for articles
    q.addKeyword(text)       # article should contain word apple
    q.addRequestedResult(RequestArticlesInfo(page=0, count = 30));  # get 30 articles that match the criteria
    res = er.execQuery(q)
    return res

def getERNewsDefault():
    #with open('/home/luis/data/mario/er/news.json') as data_file:    
    #    res = json.load(data_file)
    data_file = codecs.open('/home/luis/data/mario/er/news.json', encoding='utf-8')
    text = data_file.read()
    return json.loads(text, encoding="utf-8")

def getAllSIO():
    page = requests.get('http://portal.sio.si/gradiva')
    tree = html.fromstring(str(page.text))
    links = tree.xpath('//td[@class="style9"]/a/text()')
    #print len(links)

def getAllSioFile():
    tblEduMaterials.purge()
    f = open('/home/luis/data/mario/sio/sio4', 'r')
    for line in f:
        mat = {}
        arr =  line.rstrip('\n').split('\t')
        if len(arr) >= 9:
            mat["link"] = arr[0]
            mat["sio_link"] = arr[1]
            mat["source"] = arr[2]
            mat["sio_description"] = arr[3]
            mat["sio_level_desc"] = arr[4]
            mat["level"] = arr[5]
            mat["grade"] = arr[6]
            mat["subject_slo"] = arr[7]
            mat["subject_eng"] = arr[8]
            mat["description"] = arr[9]
            #mat["edu_content"] = arr[10]
            #print mat
            tblEduMaterials.insert(mat)

def getAllZakoni():
    tblZakoni.purge()
    f = "/home/luis/data/mario/zakoni/meta.1.json"
    with open(f) as data_file: 
        data = json.load(data_file)
        for i,d in enumerate(data["zakoni"]):
            #print i,d
            tblZakoni.insert(d)
   

def getAllOds(tblOds):
    tblOds.purge()
    f = open('/home/luis/data/mario/ods/ods.ttl', 'r')
    g = rdflib.Graph()
    result = g.parse(f, format='n3')
    #print len(g)

    objs = {}

    for subj, pred, obj in g:
        if (subj, pred, obj) not in g:
            raise Exception("It better be!")
        else:
            if subj.find("general") <> -1:
                arr = subj.encode("utf-8").split("_")
                if len(arr) > 1:
                    objs[arr[len(arr)-2]] = {}
    #print len(objs)

    for subj, pred, obj in g:
        if (subj, pred, obj) not in g:
            raise Exception("It better be!")
        else:
            if subj.find("general") <> -1:
                arr = subj.encode("utf-8").split("_")
                if len(arr) > 1:
                    id = arr[len(arr)-2]
                    if objs.has_key(id):
                        #el = {}
                        #objs[id] = el
                        #objs[id][pred.encode("utf-8")] = obj.encode("utf-8")
                        if pred.encode("utf-8") == u"http://purl.org/dc/terms/identifier":
                            objs[id]["identifier"] = obj.encode("utf-8")
                        if pred.encode("utf-8") == u"http://purl.org/dc/terms/title":
                            objs[id]["title"] = obj.encode("utf-8")
                        if pred.encode("utf-8") == u"http://purl.org/dc/terms/description":
                            objs[id]["desc"] = obj.encode("utf-8")
    br = 0
    for o in objs:
        if objs[o]["identifier"].find("http") <> -1 and objs[o].has_key("desc"):
            #print o, objs[o]
            br += 1
            tblOds.insert(objs[o])
   
    #print br

def getAllOer(tblOer):
    tblOer.purge()
    f = open('/home/luis/data/mario/oer/oer.pipe.csv', 'r')
    objs = []
    for line in f:
        oer = {}
        arr =  line.rstrip('\n').split('|')
        if len(arr) >= 9:
            oer["link"] = arr[0]
            oer["title"] = arr[1]
            oer["img_url"] = arr[3]
            oer["desc"] = arr[5]
            oer["meta"] = arr[6]
            objs.append(oer)

    tblOer.insert_multiple(objs)

    '''
    # For each foaf:Person in the store print out its mbox property.
    print("--- printing mboxes ---")
    print len(g.subjects())
    for person in g.subjects():
        print person
    '''

'''    
# get wikipedia summeries for set of keywords
def getWikipediaKeywords(keyws):
    for keyw in keyws:
        wikipedia.search(keyw)
'''

####################
# Indexing
####################

# create index of searchable researchers using whoosh index
def createIndexRsr(path, tblRsr):
    schema = Schema(fname=TEXT(stored=True), lname=TEXT(stored=True), id=TEXT(stored=True), mstid=TEXT(stored=True),\
science=TEXT(stored=True), scienceCode=TEXT(stored=True), field=TEXT(stored=True), subfield=TEXT(stored=True), keyws_en=TEXT(stored=True), keyws_sl=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/rsr", schema)

    writer = index.writer()
    for rsr in tblRsr.all():
        content = ""
        s = u""
        s_code = u""
        f = u""
        sub = u""
        keyws_en = u""
        keyws_sl = u""
        if rsr.has_key('science'):
            s = rsr['science']['#text']
            s_code = rsr['science']['@code']
            content += " "+rsr['science']['#text']
        if rsr.has_key('field'):
            f = rsr['field']['#text']
            content += " "+rsr['field']['#text']
        if rsr.has_key('subfield'):
            sub = rsr['subfield']['#text']
            content += " "+rsr['subfield']['#text']
        if rsr.has_key('keyws_en'):
            keyws_en = rsr['keyws_en']['@keyws']
            content += " "+rsr['keyws_en']['@keyws']
        if rsr.has_key('keyws_sl'):
            keyws_sl = rsr['keyws_sl']['@keyws']
            content += " "+rsr['keyws_sl']['@keyws']

        if content != "":
            print rsr["@id"]+": "+content
            writer.add_document(lname=rsr['fname'], fname=rsr['lname'], id=rsr['@id'], mstid=rsr['@mstid'],\
science=s, scienceCode=s_code, field=f, subfield=sub, keyws_en=keyws_en, keyws_sl=keyws_sl, content=content) 
    
    writer.commit()
    return index

def createIndexRsrKeyws(path, tblRsr):
    schema = Schema(keyws=TEXT(stored=True), freq=NUMERIC(stored=True))
    
    if not os.path.exists(path+"whooshindex/rsrkeyws"):
        os.makedirs(path+"whooshindex/rsrkeyws")

    index = create_in(path+"whooshindex/rsrkeyws", schema)
    
    keywsdict = {}
    writer = index.writer()

    for rsr in tblRsr.all():
        keyws = []
        if rsr.has_key('keyws_en'):
            content = rsr['keyws_en']['@keyws']
            content = content.lower()
            content = content.replace(';', ',')
            keyws = content.split(',')
        if len(keyws) > 0:
            for keyw in keyws:
                keyw = keyw.rstrip('.').strip()
                if not keywsdict.has_key(keyw):
                    keywsdict[keyw] = 1
                else:
                    keywsdict[keyw] += 1
    
    # put all unique keywords into index
    for i,k in enumerate(keywsdict):
        print i,k,keywsdict[k]
        writer.add_document(keyws=k, freq=keywsdict[k])
    
    writer.commit()
    return index

# create index of searchabe projects using whoosh. Index is called prj
def createIndexPrj(path, tblPrj):
    schema = Schema(name=TEXT(stored=True), id=TEXT(stored=True), startdate=TEXT(stored=True), enddate=TEXT(stored=True), mstid=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/prj", schema)
    
    writer = index.writer()
    for prj in tblPrj.all():
        content = ""
        if prj.has_key('name'):
            content += " "+prj['name']
        if prj.has_key('keyws_en'):
            content += " "+prj['keyws_en']
        if prj.has_key('abstr_en'):
            content += " "+prj['abstr_en']
        if prj.has_key('sign_dom_en'):
            content += " "+prj['sign_dom_en']
        if prj.has_key('sign_world_en'):
            content += " "+prj['sign_world_en']

        if content != "" and prj.has_key('name'):
            print prj["@id"]+": "+content
            writer.add_document(name=prj['name'], id=prj["@id"], startdate=prj['@startdate'], enddate=prj['@enddate'], mstid=prj['@mstid'], content=content)
 
    writer.commit()
    return index

def createIndexZakoni(path, tblZakoni):
    schema = Schema(name=TEXT(stored=True), id=TEXT(stored=True), startdate=TEXT(stored=True), enddate=TEXT(stored=True), mstid=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/prj", schema)
    
# create index of searchable organizations using whoosh stored as org
def createIndexOrg(path, tblOrg):
    schema = Schema(name=TEXT(stored=True), city=TEXT(stored=True), science=TEXT(stored=True), mstid=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/org", schema)

    writer = index.writer()
    for org in tblOrg.all():
        content = u""
        science = u""
        name = u""
        if org.has_key('name'):
            name = org['name']
            content += " "+org['name']
        if org.has_key('classification'):
            if bool(type(org['classification']) is list):
                for c in org['classification']:
                    if c.has_key('@sci_descr'):
                        content += " "+c['@sci_descr']
                        if c['@weight'] == u'1':
                            science = c['@sci_descr']
        if org.has_key('city'):
            city = org['city']

        if content != "" and org.has_key('name'):
            print org["@id"]+": "+content
            writer.add_document(name=name, city=city, science=science, content=content)

    writer.commit()
    return index

# create index of searchable sio
def createIndexSio(path, tblEduMaterials):
    schema = Schema(link=TEXT(stored=True), sio_link=TEXT(stored=True), source=TEXT(stored=True), sio_description=TEXT(stored=True), sio_level_desc=TEXT(stored=True), level=TEXT(stored=True), grade=TEXT(stored=True), subject_eng=TEXT(stored=True), subject_slo=TEXT(stored=True), content=TEXT(stored=True))
    index = create_in(path+"whooshindex/sio", schema)

    writer = index.writer()
    for sio in tblEduMaterials.all():
        link = u""
        sio_link = u""
        source = u""
        sio_description = u""
        sio_level_desc = u""
        level = u""
        grade = u""
        subject_eng = u""
        subject_slo = u""
        description = u""
        
        link = sio["link"]
        sio_link = sio["sio_link"]
        source = sio["source"]
        sio_description = sio["sio_description"]
        sio_level_desc = sio["sio_level_desc"]
        level = sio["level"]
        grade = sio["grade"]
        subject_eng = sio["subject_eng"]
        subject_slo = sio["subject_slo"]
        description = sio["description"]

        print sio_description,description 
        writer.add_document(link=link, sio_link = sio_link, source=source, sio_description=sio_description, sio_level_desc=sio_level_desc, level=level, grade=grade, subject_eng=subject_eng, subject_slo=subject_slo, content=description)

    writer.commit()
    return index

# create index of searchable ods
def createIndexOds(path, tblOds):
    schema = Schema(link=TEXT(stored=True), content=TEXT(stored=True))
    index = create_in(path+"whooshindex/ods", schema)
    writer = index.writer()
    for ods in tblOds.all():
        link = u""
        description = u""
        link = ods["identifier"]
        description = ods["desc"]
        print link,description
        writer.add_document(link=link, content=description)

    writer.commit()
    return index

# create index of searchable videolectures using whoosh
def createIndexLec(path, tblLec):
    schema = Schema(title=TEXT(stored=True), url=TEXT(stored=True), desc=TEXT(stored=True), recorded=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/lec", schema)

    writer = index.writer()
    content = u""
    for i,lec in enumerate(tblLec.all()):
        title = u""
        type = u""
        lang = u""
        url = u""
        desc = u""
        recorded = u""
        content = u""
        if lec.has_key('title'):
            title = lec['title']
            content += " "+lec['title']
        if lec.has_key('url'):
            url = lec['url']
        if lec.has_key('recorded'):
            recorded = lec['recorded']
            content += " "+lec['recorded']
        if lec.has_key('text'):
            if lec['text'].has_key('desc'):
                desc = lec['text']['desc']
                content += " "+lec['text']['desc']
            if lec['text'].has_key('title'):
                title = lec['text']['title']
                content += " "+lec['text']['title']

        if content != "":
            print lec["url"]+": "+str(i)
            writer.add_document(title=title, type=type, url=url, lang=lang, desc=desc, recorded=recorded, content=content)

    writer.commit()
    return index

# Create index for quick searching of connection between researchers and projects
def createIndexRsrPrj(path, tblRsrPrj):
    schema = Schema(prjmstid=TEXT(stored=True), prjid=TEXT(stored=True), rsrid=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/rsrprj", schema)
    writer = index.writer()
    for i,rsrprj in enumerate(tblRsrPrj.all()):
        rsrid = rsrprj['rsrid']
        prjid = rsrprj['prjid:']
        prjmstid = rsrprj['prjmstid']
        writer.add_document(prjmstid=prjmstid, prjid=prjid, rsrid=rsrid, content=rsrid)
    writer.commit()
    return index

# Create index for quick searching of connection between researchers and projects
def createIndexPrjRsr(tblRsrPrj):
    schema = Schema(prjmstid=TEXT(stored=True), prjid=TEXT(stored=True), rsrid=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/prjrsr", schema)
    writer = index.writer()
    for i,rsrprj in enumerate(tblRsrPrj.all()):
        rsrid = rsrprj['rsrid']
        prjid = rsrprj['prjid:']
        prjmstid = rsrprj['prjmstid']
        writer.add_document(prjmstid=prjmstid, prjid=prjid, rsrid=rsrid, content=prjid)
    writer.commit()
    return index

def createIndexRsrRsr(tblRsrPrjCollW):
    schema = Schema(rsrid1=TEXT(stored=True), rsrid2=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/rsrrsr", schema)
    writer = index.writer()
    for i,edge in enumerate(tblRsrPrjCollW.all()):
        rsrid1 = edge['rsrid1']
        rsrid2 = edge['rsrid2']
        writer.add_document(rsrid1=rsrid1, rsrid2=rsrid2, content=rsrid1+"-"+rsrid2)
    writer.commit()
    return index

def createIndexOer(path, tblOer):
    schema = Schema(link=TEXT(stored=True), title=TEXT(stored=True), img_url=TEXT(stored=True), desc=TEXT(stored=True), meta=TEXT(stored=True), content=TEXT)
    index = create_in(path+"whooshindex/oer", schema)
    writer = index.writer()
    objs = []
    for i,oer in enumerate(tblOer.all()):
        link = oer['link']
        title = oer['title']
        img_url = oer['img_url']
        desc = oer['desc']
        meta = oer['meta']
        content = title+' '+desc+' '+meta
        writer.add_document(link=link, title=title, img_url=img_url, desc=desc, meta=meta, content=content)
        #objs.push({'link':link, 'title':title, 'img_url':img_url, 'desc':desc, 'meta':meta, 'content':content})
    writer.commit()
    return index

# Create connections between researchers and save them into tblRsrPrjColl table of dbNets tinydb database
def createRsrPrjCollNet():
    tblRsrPrjColl.purge()
    tblRsrColl.purge()
    index = loadIndexRsrPrj()
    index1 = loadIndexPrjRsr()
    inserts = []
    inserts1 = []
    for i,rsr in enumerate(tblRsr.all()):
        vals = {}
        rsrid1 = rsr['@id']
        results = searchIndex(index, rsrid1)
        for r in results:
            prjid = r['prjid']
            res = searchIndex(index1, prjid)
            for r1 in res:
                rsrid2 = r1['rsrid']
                if not vals.has_key(rsrid2):
                    vals[rsrid2] = 1
                else:
                    vals[rsrid2] += 1
                inserts.append({'rsrid1': rsrid1, 'rsrid2': rsrid2, 'prjmstid': r['prjmstid'], 'prjid': prjid})
        inserts1.append({'rsrid': rsrid1, 'prjcoll': vals})

    print "insert multiple"
    tblRsrPrjColl.insert_multiple(inserts)
    print "insert multiple 1"
    tblRsrColl.insert_multiple(inserts1)

# Create an undirected one way network of researchers based on project collaboration
# the network is weighted
# saved in tblRrsPrjCollW table of dbNets tinydb 
def createRsrPrjCollNetWeighted():
    pairs = {}
    inserts = []
    print 'counting'
    for i,edge in enumerate(tblRsrPrjColl.all()):
        id1 = edge['rsrid1']
        id2 = edge['rsrid2']
        key = id1+","+id2
        
        if not pairs.has_key(key):
            pairs[key] = 1
        else:
            pairs[key] += 1
    print 'creating inserts'
    for i,key in enumerate(pairs):
        arr = key.split(',')
        id1 = arr[0]
        id2 = arr[1]
        weight = pairs[key]
        inserts.append({'rsrid1': id1, 'rsrid2': id2, 'weight': weight})
    print 'insert multiple'
    tblRsrPrjCollW.insert_multiple(inserts)

########################
# Loading and searching
########################
 
def loadIndexRsr(path):
    return windex.open_dir(path+"whooshindex/rsr")

def loadIndexSio(path):
    return windex.open_dir(path+"whooshindex/sio")

def loadIndexOds(path):
    return windex.open_dir(path+"whooshindex/ods")

def loadIndexOer(path):
    return windex.open_dir(path+"whooshindex/oer")

def loadIndexRsrKeyws(path):
    return windex.open_dir(path+"whooshindex/rsrkeyws")

def loadIndexPrj(path):
    return windex.open_dir(path+"whooshindex/prj")

def loadIndexOrg(path):
    return windex.open_dir(path+"whooshindex/org")

def loadIndexLec(path):
    return windex.open_dir(path+"whooshindex/lec")

def loadIndexRsrPrj(path):
    return windex.open_dir(path+"whooshindex/rsrprj")

def loadIndexPrjRsr(path):
    return windex.open_dir(path+"whooshindex/prjrsr")

def loadIndexRsrRsr(path):
    return windex.open_dir(path+"whooshindex/rsrrsr")

def searchIndex(index, text):
    out = []
    with index.searcher() as searcher:
        parser = QueryParser("content", index.schema)
        myquery = parser.parse(text)
        results = searcher.search(myquery, limit=None)
        for res in results:
            out.append(dict(res))
    return out

def searchIndexLimitedDef(index, text, limit):
    out = []
    with index.searcher() as searcher:
        parser = QueryParser("content", index.schema)
        myquery = parser.parse(text)
        results = searcher.search(myquery, limit=limit)
        for res in results:
            out.append(dict(res))
    return out

def searchIndexLimited(index, text, limit):
    out = []
    with index.searcher() as searcher:
        parser = QueryParser("content", index.schema)
        myquery = parser.parse(text)
        results = searcher.search(myquery, limit=None)
        for res in results[0:limit]:
            out.append(dict(res))
    return out, len(results)

def searchIndexSioAdv(index, text):
    out = []
    arg = json.loads(text)
    name = ""
    grade = ""
    level = ""
    text = ""
    if arg.has_key("name"):
        name = arg["name"]
    if arg.has_key("grade"):
        grade = arg["grade"]
    if arg.has_key("level"):
        level = arg["level"]
    if arg.has_key("text"):
        text = arg["text"]

    with index.searcher() as searcher:
        if arg.has_key("text"):
            parser = QueryParser("content", index.schema)
            myquery = parser.parse(text)
            results = searcher.search(myquery, limit=None)
        else:
            results = tblEduMaterials.all()

        for res in results:
            add = True
            res = dict(res)
            if arg.has_key("name"):
                if res["subject_eng"] != name:
                    add = False
            if arg.has_key("grade"):
                if res["grade"] != grade:
                    add = False
            if arg.has_key("level"):
                if res["level"] != level:
                    add = False
            if add == True:
                out.append(res)
                
    return out	

def searchIndexRsrKeyws(index, text):
    out = []
    with index.searcher() as searcher:
        parser = QueryParser("keyws", index.schema)
        myquery = parser.parse(text)
        results = searcher.search(myquery, limit=None)
        for res in results:
            out.append(dict(res))
    return out

def searchIndexRsrKeywsAutocomplete(index, text):
    out = []
    with index.searcher() as searcher:
        parser = QueryParser("keyws", index.schema)
        myquery = parser.parse(text+"*")
        results = searcher.search(myquery, limit=None)
        for res in results:
            obj = dict(res)
            out.append(obj["keyws"])
    return out

# Get value from arbitrary cache table for arbitrary query
def getCache(tbl, text):
    return tbl.search(where('query') == text)

#########################
# Special constructs
########################

#Get unique SIO items
def getUniqSio():
    data = tblEduMaterials.all()
    grades = {}
    levels = {}
    names = {}
    grade = []
    level = []
    name = []
    for d in data:
        grades[d["grade"]] = 1
        levels[d["level"]] = 1
        names[d["subject_eng"]] = 1

    for g in grades:
        grade.append(g)

    for n in names:
        name.append(n)

    for l in levels:
        level.append(l)

    res = {"grades":grade, "names":name, "levels":level}
    return res

# Create graph based on subset of researchers
def graphRsrPrj(path, rsrs):
    index = loadIndexRsrRsr(path)
    ids = []
    nodes = []
    for i,rsr in enumerate(rsrs):
        rsrid = rsr['id']
        ids.append(rsrid)

    edges = []
    print 'length',len(ids)
    if len(ids) > 360:
        ids = ids[0:359]
        print 'length',len(ids)

    l = len(ids)
    degree = {}
    for i in range(0,l-2):
        for j in range(i+1,l-1):
            id1 = ids[i]
            id2 = ids[j]
            res =searchIndex(index,id1+"-"+id2)
            if len(res) > 0:

                # node degres
                if not degree.has_key(id1):
                    degree[id1] = 1
                else:
                    degree[id1] += 1
                if not degree.has_key(id2):
                    degree[id2] = 1
                else:
                    degree[id2] += 1

                # edges
                edges.append({'rsrid1':id1, 'rsrid2': id2})

    for i,rsr in enumerate(rsrs):
        rsrid = rsr['id']
        size = 1
        if degree.has_key(rsrid):
            size = degree[rsrid]

        nodes.append({'id': rsrid, 'name':  rsr['fname']+" "+rsr['lname'],\
'x':randint(0,100), 'y':randint(0,100), 'science': rsr['science'], 'color': rsr['scienceCode'], 'degree':size})

    return {'nodes': nodes, 'edges': edges}

def getPrjHistogram(prjs):
    hist = {}
    for i,prj in enumerate(prjs):
        if prj.has_key('startdate'):
            startdate = prj['startdate']
            year = startdate.split('.')[2]
            if not hist.has_key(year):
                hist[year] = 1
            else:
                hist[year] += 1
    min = 99999
    max = -1 
    for key in hist:
        if int(key) < min:
           min = int(key)
        if int(key) > max:
           max = int(key)
    
    for y in range(min,max):
        if not hist.has_key(str(y)):
            hist[str(y)] = 0

    return hist

# get related keywords based - on keywords of related researchers
def getRelatedKeywsRelRsr(rsrs):
    hist = {}
    for i,rsr in enumerate(rsrs):
        #/print rsr
        if rsr.has_key('keyws_en'):
            keyws = re.split('; |, |;|,|\*|\n', rsr['keyws_en'])
            for keyw in keyws:
                if keyw != "":
                    keyw = keyw.lower().rstrip('.')
                    if not hist.has_key(keyw):
                        hist[keyw] = 1
                    else:
                        hist[keyw] += 1

    sorted_hist = OrderedDict(sorted(hist.items(), reverse=True, key=lambda x: x[1]))
    out = []
    order = 1
    for k, v in sorted_hist.items():
        out.append({'keyws':k, 'rank':order, 'freq':v})
        order += 1

    return out

def getRelatedClassificationRelRsr(rsrs):
    sci_hist = {}
    field_hist = {}
    subfield_hist = {}

    for i,rsr in enumerate(rsrs):
        if rsr.has_key('science'):
            science = rsr['science']
            if science != "":
                if not sci_hist.has_key(science):
                    sci_hist[science] = 1
                else:
                    sci_hist[science] += 1
        
        if rsr.has_key('field'):
            if rsr.has_key('science'):
                science = rsr['science']
            field = rsr['field']

            if field != "":
                if not field_hist.has_key(science+"_"+field):
                    field_hist[science+"_"+field] = 1
                else:
                    field_hist[science+"_"+field] += 1

        if rsr.has_key('subfield'):
            if rsr.has_key('science'):
                science = rsr['science']
            if rsr.has_key('field'):
                field = rsr['field']

            subfield = rsr['subfield']
            if subfield != "":
                if not subfield_hist.has_key(science+"_"+field+"_"+subfield):
                    subfield_hist[science+"_"+field+"_"+subfield] = 1
                else:
                    subfield_hist[science+"_"+field+"_"+subfield] += 1

    sci_sorted_hist = OrderedDict(sorted(sci_hist.items(), reverse=True, key=lambda x: x[1]))
    field_sorted_hist = OrderedDict(sorted(field_hist.items(), reverse=True, key=lambda x: x[1]))
    subfield_sorted_hist = OrderedDict(sorted(subfield_hist.items(), reverse=True, key=lambda x: x[1]))

    out = {}
    sci_arr = []
    field_arr = []
    subfield_arr = []

    order = 1
    sum_sci = 0.0
    for k, v in sci_sorted_hist.items():
        sci_arr.append({'science':k, 'rank':order, 'freq':v})
        sum_sci += v
        order += 1
    
    for sub in sci_arr:
        sub['rel'] = float(sub['freq'])/sum_sci

    order = 1
    sum_field = 0.0
    for k, v in field_sorted_hist.items():
        k = k.split('_')
        field_arr.append({'science':k[0], 'field':k[1], 'rank':order, 'freq':v})
        sum_field += v
        order += 1

    for sub in field_arr:
        sub['rel'] = float(sub['freq'])/sum_field   

    order = 1
    sum_subfield = 0.0
    for k, v in subfield_sorted_hist.items():
        k = k.split('_')
        subfield_arr.append({'science':k[0], 'field': k[1],'subfield':k[2], 'rank':order, 'freq':v})
        sum_subfield += v
        order += 1

    for sub in subfield_arr:
        sub['rel'] = float(sub['freq'])/sum_subfield

    out['sciences'] = sci_arr
    out['fields'] = field_arr
    out['subfields'] = subfield_arr
    
    return out
