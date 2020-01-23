import rdflib
import sys
import os
#import time
from rdflib import *
#__requires__ = "owlready2==0.13"
#import pkg_resources
#import owlready2
from owlready2 import *

alignOnto1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentonto1')
alignOnto2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentonto2')
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')
alignMeasure = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentmeasure')
alignRelation = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentrelation')

def descendants(e):
    r = set()
    r.add(e)
    toVisit = set()
    toVisit.add(e)
    while len(toVisit) > 0:
        next = set()
        for c in toVisit:
            for d in c.subclasses():
                if d not in r:
                    r.add(d)
                    next.add(d)
        toVisit = next
    return r

def correct(v,o1,o2):
    t0 = time.process_time()
    aligned1 = {}
    aligned2 = {}

    tx1 = {}
    tx2 = {}
    l = {}
    l1 = len(o1.base_iri)
    l2 = len(o2.base_iri)
    for s in v.subjects(RDF.type, alignCell):
        e1 = v.value(s,alignEntity1, None)[l1:]
        e2 = v.value(s,alignEntity2, None)[l2:]
        if e1 not in aligned1:
            aligned1[e1] = set()
        if e2 not in aligned2:
            aligned2[e2] = set()
        aligned1[e1].add(s)
        aligned2[e2].add(s)
        tx1[s] = {}
        tx2[s] = {}
        tx1[s][s] = True
        tx2[s][s] = True
        l[s]=(s,e1,e2)

    t1 = time.process_time()
    droplist = []
    for i in l:
        ln = []
        for y in o1[l[i][1]].ancestors():
            if y.name in aligned1:
                for s in aligned1[y.name]:
                    tx1[i][s] = True
                    ln.append(y.name)
        for y in o2[l[i][2]].ancestors():
            if y.name in aligned2:
                for s in aligned2[y.name]:
                    if not s in tx1[i]:
                        if i in aligned1[l[i][1]]:
                            aligned1[l[i][1]].remove(i)
                            aligned2[l[i][2]].remove(i)
                            droplist.append(i)
                            aligned1[l[s][1]].remove(s)
                            aligned2[l[s][2]].remove(s)
                            droplist.append(s)
                        break
                    else:
                        tx2[i][s] = True
                else:
                    continue
                break
        else:
            for y in ln:
                for s in aligned1[y]:
                    if not s in tx2[i]:
                        if i in aligned1[l[i][1]]:
                            aligned1[l[i][1]].remove(i)
                            aligned2[l[i][2]].remove(i)
                            droplist.append(i)
                            aligned1[l[s][1]].remove(s)
                            aligned2[l[s][2]].remove(s)
                            droplist.append(s)
                        break
                else:
                    continue
                break

    t2 = time.process_time()

    newdrop = droplist
    newdrop = []
    for i in droplist:
        ln = []
        for y in o1[l[i][1]].ancestors():
            if y.name in aligned1:
                for s in aligned1[y.name]:
                    tx1[i][s] = True
                    ln.append(y.name)
        ld = []
        for y in descendants(o1[l[i][1]]):
            if y.name in aligned1:
                for s in aligned1[y.name]:
                    tx1[s][i] = True
                    ld.append(y.name)
        for y in o2[l[i][2]].ancestors():
            if y.name in aligned2:
                for s in aligned2[y.name]:
                    if not s in tx1[i]:
                        newdrop.append(i)
                        break
                    else:
                        tx2[i][s] = True
                else:
                    continue
                break
        else:
            for y in descendants(o2[l[i][2]]):
                if y.name in aligned2:
                    for s in aligned2[y.name]:
                        if not i in tx1[s]:
                            newdrop.append(i)
                            break
                        else:
                            tx2[s][i] = True
                    else:
                        continue
                    break
            else:
                for y in ln:
                    for s in aligned1[y]:
                        if not s in tx2[i]:
                            newdrop.append(i)
                            break
                    else:
                        continue
                    break
                else:
                    for y in ld:
                        for s in aligned1[y]:
                            if not i in tx2[s]:
                                newdrop.append(i)
                                break
                        else:
                            continue
                        break
                    else:
                        aligned1[l[i][1]].add(i)
                        aligned2[l[i][2]].add(i)
    t3 = time.process_time()
    return (newdrop,(t1-t0,t2-t1,t3-t2, len(droplist),len(newdrop)))

def printAlignment(v,out):
    sys.stderr = open(os.devnull, "w")
    out.write('<?xml version="1.0" encoding="utf-8"?>\n')
    out.write('<rdf:RDF xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment"\n')
    out.write('\txmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n')
    out.write('\txmlns:xsd="http://www.w3.org/2001/XMLSchema#">\n<Alignment>\n<xml>yes</xml>\n<level>0</level>\n<type>??</type>\n')
    out.write('<onto1><Ontology rdf:about="'+list(v.triples((None,alignOnto1,None)))[0][2].lower()+'"></Ontology></onto1>\n')
    out.write('<onto2><Ontology rdf:about="'+list(v.triples((None,alignOnto2,None)))[0][2].lower()+'"></Ontology></onto2>\n')
    for s in v.subjects(RDF.type, alignCell):
        out.write('<map>\n\t<Cell>\n')
        out.write('\t\t<entity1 rdf:resource="'+v.value(s,alignEntity1, None)+'"/>\n')
        out.write('\t\t<entity2 rdf:resource="'+v.value(s,alignEntity2, None)+'"/>\n')
        out.write('\t\t<measure rdf:datatype="xsd:float">'+v.value(s,alignMeasure, None)+'</measure>\n')
        out.write('\t\t<relation>'+v.value(s,alignRelation, None)+'</relation>\n')
        out.write('\t</Cell>\n</map>\n')
    out.write('</Alignment>\n</rdf:RDF>\n')
    sys.stderr = sys.__stderr__

def evaluateAlignment(align,onto1,onto2):
    v = rdflib.Graph().parse(align)
    ogSize = len(list(v.subjects(RDF.type, alignCell)))

    o1 = get_ontology(onto1)
    o1.load()

    o2 = get_ontology(onto2)
    o2.load()

    sys.stderr = open(os.devnull, "w") # hide reasoner verbosity
    sync_reasoner_pellet()
    sys.stderr = sys.__stderr__

    (remove,data) = correct(v,o1,o2)

    for n in remove:
        v.remove((n, None, None))
        v.remove((None, None, n))

    o = open("corrected_"+align,'w')
    printAlignment(v,o)
    o.close()

    print("Correction complete!\n===Summary===\nInput alignment: %s\tSize: %d"%(align,ogSize))
    print("Output alignment: corrected_%s\tSize %d\nTime for repair computation (greedy algorithm): %.5f seconds"%(align,ogSize-data[4],data[1]))
    print("Time for repair improvement: %.5f seconds\nPreliminary repair size (greedy algorithm):%d\nFinal repair size (after improvement step): %d\n"%(data[2],data[3],data[4]))

if __name__ == "__main__":
    if len(sys.argv) == 4:
        evaluateAlignment(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Incorrect number of parameters! Usage:\npython3 conservativity.py <alignment file> <ontology1 file> <ontology 2 file>")
