import rdflib
import sys
import os
from rdflib import *
from owlready2 import *

alignOnto1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentonto1')
alignOnto2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentonto2')
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')

def findViolations(v,o1,o2):
    a = []
    violations = []
    l1 = len(o1.base_iri)
    l2 = len(o2.base_iri)
    for s in v.subjects(RDF.type, alignCell):
        e1 = v.value(s,alignEntity1, None)[l1:]
        e2 = v.value(s,alignEntity2, None)[l2:]
        for e in a:
            if o1[e[0]] in o1[e1].ancestors():
                if o2[e[1]] not in o2[e2].ancestors():
                    violations.append((o2[e2],o2[e[1]]))
            else:
                if o2[e[1]] in o2[e2].ancestors():
                    violations.append((o1[e1],o1[e[0]]))
            if o1[e1] in o1[e[0]].ancestors():
                if o2[e2] not in o2[e[1]].ancestors():
                    violations.append((o2[e[1]],o2[e2]))
            else:
                if o2[e2] in o2[e[1]].ancestors():
                    violations.append((o1[e[0]],o1[e1]))
        a.append((e1,e2))
    return violations

def findIndirectViolations(violations):
    indViol = []
    for s,t in violations:
        for d in s.descendants():
            for a in t.ancestors():
                if a not in d.ancestors():
                    v = (d,a)
                    if v not in violations and v not in indViol:
                        indViol.append(v)
        for a in t.ancestors():
            for d in s.descendants():
                if d not in a.descendants():
                    v = (d,a)
                    if v not in violations and v not in indViol:
                        indViol.append(v)
    return indViol

def evaluateAlignment(fileName):
    v = rdflib.Graph().parse(fileName)

    onto1 = list(v.triples((None,alignOnto1,None)))[0][2]
    onto2 = list(v.triples((None,alignOnto2,None)))[0][2]
    o1 = get_ontology(onto1.lower()[7:]+".owl")
    o2 = get_ontology(onto2.lower()[7:]+".owl")
    o1.load()
    o2.load()

    t0 = time.process_time()
    violations = findViolations(v,o1,o2)
    t1 = time.process_time()
    indirect = findIndirectViolations(violations)
    t2 = time.process_time()
    nv = len(violations)
    ni = len(indirect)
    tv = t1-t0
    ti = t2-t1

    if nv > 0:
        out = open(fileName[:-4]+".violations.txt",'w')
        out.write("Conservativity violations found in alignment %s\n"%(fileName))
        out.write("Violations detected:\t%d\t\tDirect:\t%d\tIndirect:\t%d\n"%(nv+ni,nv,ni))
        out.write("Computation time:\t%f s\n"%(t2-t0))
        out.write("\tof which\t"+str(tv)+" s for the detection of direct violations\n")
        out.write("\t\t\t"+str(ti)+" s for the detection of indirect violations\n")
        out.write("\n\nDirect violations detected:\n")
        for i in violations:
            out.write(str(i)+'\n')
        out.write("\n\nIndirect violations detected:\n")
        for i in indirect:
            out.write(str(i)+'\n')
        out.close()
    return (nv,ni,tv,ti)

if __name__ == "__main__":
    out = open("violations_summary.txt",'w')
    out.write("Conservativity violations - Summary\n")
    out.write("Alignment\tViolations\tTime\n")
    for root,dirs,files in os.walk('.'):
        for f in files:
            if f[-4:]==".rdf":
                r = evaluateAlignment(f)
                out.write("%s\t%d(%d)\t%.2f(%.2f)\n"%(f,r[0]+r[1],r[1],r[2],r[3]))
    out.close()
