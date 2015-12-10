from EventRegistry.EventRegistry import *

er = EventRegistry(host = "http://eventregistry.org", logging = True)

q = QueryEvents()
q.addConcept(er.getConceptUri("Education"))
q.addRequestedResult(RequestEventsUriList())
res = er.execQuery(q)
obj = createStructFromDict(res)
uris = obj.uriList

for uri in uris[:5]:
    q = QueryEvent(uri)
    q.addRequestedResult(RequestEventInfo(["eng"]))   # get event information. concept labels should be in three langauges
    q.addRequestedResult(RequestEventArticles(0, 10))   # get 10 articles describing the event
    q.addRequestedResult(RequestEventKeywordAggr())     # get top keywords describing the event
    eventRes = er.execQuery(q)
    out = {}
    out['info'] =  eventRes[uri][u'info'][u'multiLingInfo']
    out['date'] =  eventRes[uri][u'info'][u'eventDate']
    out['uri'] = uri
    print out
