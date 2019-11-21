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

def correct(v,o1,o2):
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
            aligned1[e1] = []
        if e2 not in aligned2:
            aligned2[e2] = []
        aligned1[e1].append(s)
        aligned2[e2].append(s)
        tx1[s] = {}
        tx2[s] = {}
        tx1[s][s] = True
        tx2[s][s] = True
        l[s]=(s,e1,e2)

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
                    tx2[i][s] = True
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
    return droplist

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
            aligned1[e1] = []
        if e2 not in aligned2:
            aligned2[e2] = []
        aligned1[e1].append(s)
        aligned2[e2].append(s)
        tx1[s] = {}
        tx2[s] = {}
        tx1[s][s] = True
        tx2[s][s] = True
        l[s]=(s,e1,e2)

    violations = []
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
                            violations.append(viol)
        else:
            for y in ln:
                for s in aligned1[y]:
                    if not s in tx2[i]:
                        viol = (o2[l[i][2]],o2[l[s][2]])
                        if not viol in violations:
                            violations.append(viol)
    return violations

def findIndirectViolations(violations):
    indViol = []
    for s,t in violations:
        for d in s.descendants():
            for a in t.ancestors()-d.ancestors():
                v = (d,a)
                if v not in violations and v not in indViol:
                    indViol.append(v)
        for a in t.ancestors():
            for d in s.descendants()-a.descendants():
                v = (d,a)
                if v not in violations and v not in indViol:
                    indViol.append(v)
    return indViol

def evaluateAlignment(fileName, onlyCorrect = False, onlyDirect = False):
    v = rdflib.Graph().parse(fileName)
    ogSize = len(list(v.subjects(RDF.type, alignCell)))

    onto1 = list(v.triples((None,alignOnto1,None)))[0][2]
    onto2 = list(v.triples((None,alignOnto2,None)))[0][2]
    o1 = get_ontology(onto1.lower()[7:]+".owl")
    o2 = get_ontology(onto2.lower()[7:]+".owl")
    o1.load()
    o2.load()


    t0 = time.process_time()
    violations = []
    if not onlyCorrect:
        violations = findViolations(v,o1,o2)
    t1 = time.process_time()
    indirect = []
    if not onlyCorrect and not onlyDirect:
        indirect = findIndirectViolations(violations)
    t2 = time.process_time()
    remove = correct(v,o1,o2)
    t3 = time.process_time()

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
        c = open("corrected/"+fileName,'wb')
        c.write(v.serialize())
        c.close()
        out = open(fileName[:-4]+".violations.txt",'w')
        out.write("Conservativity violations found in alignment %s\n"%(fileName))
        if not onlyCorrect:
            if onlyDirect:
                out.write("Direct violations detected:\t%d\n"%(nv))
            else:
                out.write("Violations detected:\t%d\t\tDirect:\t%d\tIndirect:\t%d\n"%(nv+ni,nv,ni))
        out.write("Original alignment size:\t%d\nCorrected alignment size:\t%d\n"%(ogSize, resSize))
        out.write("Correction time:\t%f s\n"%(t3-t2))
        if not onlyCorrect:
            out.write("Detection time:\t%f s\n"%(t2-t0))
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
    return (nv,ni,tv,ti,ogSize,resSize,t3-t2)

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
        out.write("Alignment\tOriginal size\tResult size\tViolations\tCorrection time\tDetection time\n")
        for root,dirs,files in os.walk('.'):
            for f in files:
                if f[-4:]==".rdf":
                    print(f)
                    r = evaluateAlignment(f, onlyCorrect, onlyDirect)
                    if onlyCorrect:
                        out.write("%s\t%d\t%d\t-(-)\t%.5f\t-(-)\n"%(f,r[4],r[5],r[6]))
                    elif onlyDirect:
                        out.write("%s\t%d\t%d\t%d(-)\t%.5f\t%.5f(-)\n"%(f,r[4],r[5],r[0],r[6],r[2]))
                    else:
                        out.write("%s\t%d\t%d\t%d(%d)\t%.5f\t%.5f(%.5f)\n"%(f,r[4],r[5],r[0],r[1],r[6],r[2],r[3]))
            break
        out.close()
