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
        #print(str(e1)+'\t'+str(e2))
        l[s]=(s,e1,e2)#,len(o1[e1].descendants())+len(o2[e2].descendants()))
        
#    ls = list(l.keys())
#    ls.sort(key=lambda x: l[x][3])

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

def findViolations(v,o1,o2):
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

    violations = set()
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
                    tx2[i][s] = True
                    if not s in tx1[i]:
                        viol = (o1[l[i][1]],o1[l[s][1]])
                        if not viol in violations:
                            violations.add(viol)
        else:
            for y in ln:
                for s in aligned1[y]:
                    if not s in tx2[i]:
                        viol = (o2[l[i][2]],o2[l[s][2]])
                        if not viol in violations:
                            violations.add(viol)
    return violations

def findIndirectViolations(violations):
    indViol = set()
    for s,t in violations:
        for d in descendants(s):
            for a in t.ancestors()-d.ancestors():
                v = (d,a)
                if v not in violations and v not in indViol:
                    indViol.add(v)
        for a in t.ancestors():
            for d in descendants(s)-descendants(a):
                v = (d,a)
                if v not in violations and v not in indViol:
                    indViol.add(v)
    return indViol

def printAlignment(v,out):
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

def evaluateAlignment(fileName, onlyCorrect = False, onlyDirect = False):
    v = rdflib.Graph().parse(fileName)
    ogSize = len(list(v.subjects(RDF.type, alignCell)))

    onto1 = list(v.triples((None,alignOnto1,None)))[0][2]
    o1 = get_ontology(onto1.lower()[7:]+".owl")
    o1.load()

    onto2 = list(v.triples((None,alignOnto2,None)))[0][2]
    o2 = get_ontology(onto2.lower()[7:]+".owl")
    o2.load()

    sync_reasoner()

    t0 = time.process_time()
    violations = []
    if not onlyCorrect:
        violations = findViolations(v,o1,o2)
    t1 = time.process_time()
    indirect = []
    if not onlyCorrect and not onlyDirect:
        indirect = findIndirectViolations(violations)
    t2 = time.process_time()
    (remove,data) = correct(v,o1,o2)

    nv = len(violations)
    ni = len(indirect)
    tv = t1-t0
    ti = t2-t1

    resSize = ogSize
    if nv > 0 or onlyCorrect:
        for n in remove:
            v.remove((n, None, None))
            v.remove((None, None, n))
            resSize = len(list(v.subjects(RDF.type, alignCell)))
        o = open("corrected/"+fileName,'w')
        printAlignment(v,o)
        o.close()
        out = open(fileName[:-4]+".violations.txt",'w')
        out.write("Conservativity violations found in alignment %s\n"%(fileName))
        if not onlyCorrect:
            if onlyDirect:
                out.write("Direct violations detected:\t%d\n"%(nv))
            else:
                out.write("Violations detected:\t%d\t\tDirect:\t%d\tIndirect:\t%d\n"%(nv+ni,nv,ni))
        out.write("Original alignment size:\t%d\nCorrected alignment size:\t%d\n"%(ogSize, resSize))
        out.write("\tGreedy algorithm repair size:\t%d\n\tImproved repair size:\t\t%d\n\n"%(data[3],data[4]))
        out.write("Correction time:\t%f s\n"%(data[1]+data[2]))
        out.write("\tof which\t%f s for the greedy algorithm stage\n"%(data[1]))
        out.write("\t\t\t%f s for the result improvement stage\n"%(data[2]))
        if not onlyCorrect:
            out.write("\nDetection time:\t%f s\n"%(t2-t0))
            if not onlyDirect:
                out.write("\tof which\t"+str(tv)+" s for the detection of direct violations\n")
                out.write("\t\t\t"+str(ti)+" s for the detection of indirect violations\n")
            out.write("\n\nDirect violations detected:\n")
            for i in violations:
                out.write(str(i)+'\n')
            if not onlyDirect:
                out.write("\n\nIndirect violations detected:\n")
                for i in indirect:
                    out.write(str(i)+'\n')
        out.close()

    s = open("violations_summary.txt",'a')
    if onlyCorrect:
         s.write("%s\t%d\t%d\t%d\t%.5f\t%.5f\t-(-)\t-(-)\n"%(fileName,ogSize,data[3],data[4],data[1],data[2]))
    elif onlyDirect:
         s.write("%s\t%d\t%d\t%d\t%.5f\t%.5f\t%d(-)\t%.5f(-)\n"%(fileName,ogSize,data[3],data[4],data[1],data[2],nv,tv))
    else:
         s.write("%s\t%d\t%d\t%d\t%.5f\t%.5f\t%d(%d)\t%.5f(%.5f)\n"%(fileName,ogSize,data[3],data[4],data[1],data[2],nv,ni,tv,ti))
    s.close()

    return (nv,ni,tv,ti,ogSize,data[1],data[2],data[3],data[4])

if __name__ == "__main__":
    onlyCorrect = False
    onlyDirect = False
    args = 1
    if "-d" in sys.argv:
        onlyDirect = True
        args += 1
    elif "-c" in sys.argv:
        onlyCorrect = True
        args += 1
    if len(sys.argv) > args:
        for f in sys.argv[1:]:
            if f != "-c" and f != "-d":
                evaluateAlignment(f, onlyCorrect, onlyDirect)
    else:
        out = open("violations_summary.txt",'w')
        out.write("Conservativity violations - Summary\n")
        out.write("Alignment\tOriginal size\tGreedy repair size\tImproved repair size\tGreedy repair time\tImprovement time\t\tViolations\tDetection time\n")
        for root,dirs,files in os.walk('.'):
            for f in files:
                if f[-4:]==".rdf":
                    print(f)
                    (violations, indirectV, detectTime, indirectTime, originalSize, greedyTime, improvTime, greedySize, improvSize) = evaluateAlignment(f, onlyCorrect, onlyDirect)
                    if onlyCorrect:
                        out.write("%s\t%d\t%d\t%d\t%.5f\t%.5f\t-(-)\t-(-)\n"%(f,originalSize,greedySize,improvSize,greedyTime,improvTime))
                    elif onlyDirect:
                        out.write("%s\t%d\t%d\t%d\t%.5f\t%.5f\t%d(-)\t%.5f(-)\n"%(f,originalSize,greedySize,improvSize,greedyTime,improvTime,violations,detectTime))
                    else:
                        out.write("%s\t%d\t%d\t%d\t%.5f\t%.5f\t%d(%d)\t%.5f(%.5f)\n"%(f,originalSize,greedySize,improvSize,greedyTime,improvTime,violations,indirectV,detectTime,indirectTime))
            break
        out.close()
