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

dbSicris = TinyDB('./data/tinydb/sicris.json')
dbVideoLectures = TinyDB('./data/tinydb/videolectures.json')
tblRsr = dbSicris.table("rsr")
tblPrj = dbSicris.table("prj")
tblOrg = dbSicris.table("org")
tblLec = dbVideoLectures.table("lec")

dbNyt = TinyDB('./data/tinydb/nyt.json')
tblNyt = dbNyt.table('nyt')

clusterIID = {}
articleIID = {}
cach = {}

def loadNytText():
    with open('/media/mario/My Book/mario/sopho/nyt/nyt/nyt-text/texts.txt', "r") as ins:
        prev_id = -1
        pos = ins.tell()
        line = ins.readline()
        cid = line.split('#')[0]
        print 'pos',str(pos)
        clusterIID[prev_id] = pos
        prev_id = cid
        if i%100000==0:
            print i

def loadNytCluster():
    with open('/media/mario/My Book/mario/sopho/nyt/nyt/nyt-text/cluster_article_id.txt', "r") as ins:
        ins.readline()
        prev_id = -1
        pos = ins.tell()
        line = ins.readline()
        cid = line.split('\t')[0]
        print 'pos',str(pos)
        articleIID[prev_id] = pos
        prev_id = cid
        if i%100000==0:
            print i

def searchNytClusterIds(inIds):
    inIds = inIds.split(',')
    arr = []
    for inId in inIds[0:10]:
        arr.append(searchNytClusterId(inId))
    return arr

def searchNytClusterId(inId):
    if not cach.has_key(inId):
        return fileSearch(inId)
    else:
        return cachSearch(inId)

def cachSearch(inId):
    if tblNyt.get(where('id') == inId):
        print "tblNyt return"
        return tblNyt.get(where('id') == inId)
    else:
        return cach[inId]

def count_nyt():
    return len(cach)

def fileSearch(inId):
    lnum = -1
    text = ""
    title = ""
    if articleIID.has_key(inId):
        lnum = articleIID[inId]
    cid = ""

    if lnum != -1:
        lnum += 2
        fo = open('/media/mario/My Book/mario/sopho/nyt/nyt/nyt-text/cluster_article_id.txt',"rw+")
        fo.seek(lnum,0)
        line = fo.readline()
        print "line1: ",line
        cid = line.split('\t')[1].rstrip('\n')
        #with open('/media/mario/My Book/mario/sopho/nyt/nyt/nyt-text/cluster_article_id.txt') as f:
            #line = next(islice(f, lnum - 1, lnum))
            #cid = line.split('\t')[1].rstrip('\n')
            
   
    if clusterIID.has_key(cid):
        lnum = clusterIID[cid]
        fo = open('/media/mario/My Book/mario/sopho/nyt/nyt/nyt-text/texts.txt',"rw+")
        fo.seek(lnum,0)
        line = fo.readline()
        print "line2:", line
        text = line.split('#')[1].rstrip('\n')
        #with open('/media/mario/My Book/mario/sopho/nyt/nyt/nyt-text/texts.txt') as f:
            #line = next(islice(f, lnum - 1, lnum))
            #text = line.split('#')[1].rstrip('\n')

        fo = open('/media/mario/My Book/mario/sopho/nyt/nyt/nyt-text/titles.txt',"rw+")
        fo.seek(lnum,0)
        line = fo.readline()
        print "line3:", line
        #line = next(islice(f, lnum - 1, lnum))
        title = line.split('#')[2].rstrip('\n')
        #with open('/media/mario/My Book/mario/sopho/nyt/nyt/nyt-text/titles.txt') as f:
            #line = next(islice(f, lnum - 1, lnum))
            #title = line.split('#')[2].rstrip('\n')
     
    out = {}
    out['title'] = title
    out['text'] = text
    out['id'] = inId
    out['cid'] = cid

    cach[inId] = out
    if tblNyt.get(where('id') == inId) == None:
        tblNyt.insert(out)
        print 'tblNyt insert'

    return out
      
# from sorted dict to dict
def to_dict(input_ordered_dict):
    return loads(dumps(input_ordered_dict))

def createClient():
    url = "http://webservice.izum.si/ws-cris/CrisService.asmx?WSDL"
    return suds.client.Client(url)

def createClientVideoLectures():
    url = "http://videolectures.net/site/stats/lectures.json"
    request = urllib2.Request(url)
    base64string = base64.encodestring('%s:%s' % ('Gaber', 'Ylat0r0g')).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)   
    return request
 
def getAllVideoLectures(client):
    shutil.copyfile('./data/tinydb/videolectures.json', './data/tinydb/videolectures.json.backup')
    result = urllib2.urlopen(client)
    lectures = json.loads(result.read())
    length = len(lectures)
    for i,l in enumerate(lectures):
        tblLec.insert(lectures[l])
        if i%10000 == 0:
            print i

def getSessionId(client):
    return client.service.GetSessionID("si","webServiceIJS","3SW|!Bz5*8k9")

def getAllRsr(client, sessionId):
    shutil.copyfile('./data/tinydb/sicris.json', './data/tinydb/sicris.json.backup')
    methodCall = "Sicris_app_UI.Researcher.SearchSimple.eng.public.utf-8.mstid.%.1.-1"
    tblRsr.purge()
    result = client.service.Retrieve("si", "RSR", methodCall, "", sessionId)
    res = result.Records
    obj = xmltodict.parse(res)
    for rsr in obj['CRIS_RECORDS']['RSR']:
        tblRsr.insert(to_dict(rsr))

def getAllRsrKeyws(client, sessionId, lang, rsrs):
    shutil.copyfile('./data/tinydb/sicris.json', './data/tinydb/sicris.json.backup')
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

def getPrj(client, sessionId, lang, prjid):
    methodCall = "Sicris_app_UI.Project.SearchSimple.PRJ."+lang+".public.utf-8.id."+prjid+".1.1"
    results = client.service.Retrieve("SI", "PRJ", methodCall, "", sessionId)
    res = results.Records
    obj = {}

    try:
        obj = xmltodict.parse(res)
        obj = to_dict(obj)
    except:
        pass

    print obj

def getAllPrj(client, sessionId, lang):
    shutil.copyfile('./data/tinydb/sicris.json', './data/tinydb/sicris.json.backup')
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
        print i,len(obj['CRIS_RECORDS']['PRJ'])
        tblPrj.insert(to_dict(prj))

def getAllPrjDetails(client, sessionId, lang, prjs):
    shutil.copyfile('./data/tinydb/sicris.json', './data/tinydb/sicris.json.backup')
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
        
        print i

def getAllOrg(client, sessionId, lang):
    shutil.copyfile('./data/tinydb/sicris.json', './data/tinydb/sicris.json.backup')
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
        print i,len(obj['CRIS_RECORDS']['ORG'])
        tblOrg.insert(to_dict(org))

def getAllOrgDetails(client, sessionId, lang, orgs):
    shutil.copyfile('./data/tinydb/sicris.json', './data/tinydb/sicris.json.backup')
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
        print i

def createIndexRsr(tblRsr):
    schema = Schema(fname=TEXT(stored=True), lname=TEXT(stored=True), id=TEXT(stored=True), mstid=TEXT(stored=True),\
science=TEXT(stored=True), field=TEXT(stored=True), subfield=TEXT(stored=True), content=TEXT)
    index = create_in("./data/whooshindex/rsr", schema)

    writer = index.writer()
    for rsr in tblRsr.all():
        content = ""
        s = u""
        f = u""
        sub = u""
        if rsr.has_key('science'):
            s = rsr['science']['#text']
            content += " "+rsr['science']['#text']
        if rsr.has_key('field'):
            f = rsr['field']['#text']
            content += " "+rsr['field']['#text']
        if rsr.has_key('subfield'):
            sub = rsr['subfield']['#text']
            content += " "+rsr['subfield']['#text']
        if rsr.has_key('keyws_en'):
            content += " "+rsr['keyws_en']['@keyws']
        if rsr.has_key('keyws_sl'):
            content += " "+rsr['keyws_sl']['@keyws']

        if content != "":
            print rsr["@id"]+": "+content
            writer.add_document(lname=rsr['fname'], fname=rsr['lname'], id=rsr['@id'], mstid=rsr['@mstid'],\
science=s, field=f, subfield=sub, content=content) 
    
    writer.commit()
    return index

def createIndexPrj(tblPrj):
    schema = Schema(name=TEXT(stored=True), startdate=TEXT(stored=True), enddate=TEXT(stored=True), mstid=TEXT(stored=True), content=TEXT)
    index = create_in("./data/whooshindex/prj", schema)
    
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
            writer.add_document(name=prj['name'], startdate=prj['@startdate'], enddate=prj['@enddate'], mstid=prj['@mstid'], content=content)
 
    writer.commit()
    return index

def createIndexOrg(tblOrg):
    schema = Schema(name=TEXT(stored=True), city=TEXT(stored=True), science=TEXT(stored=True), mstid=TEXT(stored=True), content=TEXT)
    index = create_in("./data/whooshindex/org", schema)

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


def loadIndexRsr():
    return windex.open_dir("./data/whooshindex/rsr")

def loadIndexPrj():
    return windex.open_dir("./data/whooshindex/prj")

def loadIndexOrg():
    return windex.open_dir("./data/whooshindex/org")

def searchIndex(index, text):
    out = []
    with index.searcher() as searcher:
        parser = QueryParser("content", index.schema)
        myquery = parser.parse(text)
        results = searcher.search(myquery, limit=None)
        for res in results:
            out.append(dict(res))
    return out
