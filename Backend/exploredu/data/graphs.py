import suds
import xmltodict
from json import loads, dumps
from collections import OrderedDict
import time
import urllib2
import base64
import json
import re
from itertools import islice
from random import randint
import requests
import snap

def remove_loops(G):
    for i in G.Nodes():
        temp=i.GetId()
        if G.IsEdge(temp,temp):
            G.DelEdge(temp,temp)

def delete_vertex(v_ID, S, G, node_domin, histogram):
    S.append(v_ID)
    global centrality,k
    GDC_gain=vertex_score(v_ID, G, node_domin)
    for i in G.GetNI(v_ID).GetOutEdges():
        decreaseContribution(i, G, node_domin, histogram)
        node_domin[i]=True
        edges_to_i = [ii for ii in G.GetNI(i).GetInEdges()]
        edges_to_i.remove(v_ID)
        for j in edges_to_i:
            decreaseContribution(j, G, node_domin, histogram)
            G.DelEdge(j,i)
    for i in G.GetNI(v_ID).GetInEdges():
        decreaseContribution(i, G, node_domin, histogram)
    remove_from_contr_list(v_ID,GDC_gain)
    G.DelNode(v_ID)
    if best_contribution==-1:
        global dominated
        dominated = True
    centrality+=GDC_gain
    return centrality

def take_best(histogram, best_contribution, S, G, node_domin):
    return delete_vertex(histogram[best_contribution].__iter__().next(), S, G, node_domin, histogram)

def decreaseContribution(v, G, node_domin, histogram):  # for managing contribution table; O(1)
    contribution = vertex_score(v, G, node_domin)
    remove_from_contr_list(v,contribution, histogram)
    add_to_contr_list(v,contribution-1, histogram)

def add_to_contr_list(v,score, histogram): #for managing contribution table; O(1)
    if score not in histogram.keys():
        histogram[score]=set([v])
    else:
        histogram[score].add(v)

def remove_from_contr_list(v,score, histogram): #for managing contribution table; O(1)
    histogram[score].remove(v)
    if histogram[score]==set():
        histogram.pop(score)
        global best_contribution
        best_contribution = max(histogram.keys())

def vertex_score(v, G, node_domin):
    return G.GetNI(v).GetOutDeg() - (1 if node_domin[v] else 0)

# centralization functions
def updateCentralizationVariables():
    global k,A,B,C,sum_vector
    A=n/float((n-k-1)*(n-k))    
    C=n/float(n-k-1) 
    B=0
    for i in sum_vector:
        sum_vector[i]*=(n-i-k-1)/float(n-k-2)
        B+=sum_vector[i]*degree_distribution[i]

def gcentrality():
    #init. phase
    print("Initializing graph...")
    G = snap.GenRndGnm(snap.PNGraph, 10, 30)

    print("done\n\nNow removing loops...")
    remove_loops(G)
    histogram = {}
    S=[]
    node_domin = {}
    dominated = False
    centrality = 0
    print("done.\n\nSetting up degree distribution...")
    for i in G.Nodes():
        node_domin[i.GetId()]=False
        outdegree = i.GetOutDeg()
        add_to_contr_list(i.GetId(),outdegree, histogram)
    best_contribution = max(histogram.keys())

    # centralization things WITH DENOMINATOR
    n=G.GetNodes()
    k=0
    degree_distribution = {i:len(histogram[i]) for i in histogram}
    sum_vector={i:1/float(n-1) for i in histogram}

    print("done.\n\nBegin testing...")  # testing
    while not dominated:
        k=k+1
        take_best(histogram, best_contribution, S, G, node_domin)
        updateCentralizationVariables()
        centralization = A*centrality+B-C
        print (str(centralization)+"\n")
    print("done.")
