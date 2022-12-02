from graphviz import Digraph
from datetime import datetime
import re


def graphGenerator(nodes, edges):
    g = Digraph('G', filename='graph.gv', format='pdf')

    addFileNodes(g, nodes)
    addIPNodes(g, nodes)
    addProcessNodes(g, nodes)

    for edge in edges:
        g.edge(edge['x'], edge['y'], label=edge['label'])

    g.view()
    # print(g.source)
    # g.render('test.pdf', view=True)


def addProcessNodes(g, nodes):
    ##add process nodes:
    processes = filter(lambda node: node[1] == 'process', nodes)
    g.attr('node', shape='box')
    for eachProcess in processes:
        g.node(eachProcess[0], eachProcess[0])


def addFileNodes(g, nodes):
    ##add process nodes:
    files = filter(lambda node: node[1] == 'file', nodes)
    g.attr('node', shape='ellipse')
    for eachFile in files:
        g.node(eachFile[0], eachFile[0])


def addIPNodes(g, nodes):
    ##add process nodes:
    ips = filter(lambda node: node[1] == 'ip', nodes)
    g.attr('node', shape='diamond')
    for eachIP in ips:
        g.node(eachIP[0], eachIP[0])


def parseTextFile(fileName):
    lineContents = extractLineContents(fileName)
    i = 0

    # filter out exit events only:

    tupleList = list()

    nodes = set()
    edges = list()
    for each in lineContents:
        # if line contents are not empty
        if len(each) > 0 and each[5] == '<':
            #print(each)
            # extracting information:
            finalProcessName = processSubjectName(each)
            operation = each[6]
            obj = each[9].replace('fdName=', '').replace(":","_").replace("->", "=>")
            eventEndTime = int(each[1])
            latency = int(each[10].replace('latency=', ''))
            eventStartTime = eventEndTime - latency
            fdType = each[8].replace('fdtype=','')

            if len(obj) == 0:
                continue

            ##Constructing Tuple
            eachEvent = (finalProcessName, obj, operation, eventStartTime, eventEndTime, latency)
            #print(eachEvent)
            tupleList.append(eachEvent)

            ##Node Addition:
            nodes.add((finalProcessName, "process"))
            if fdType == 'ipv4' or fdType == 'ipv6':
                nodes.add((obj, "ip"))
            else:
                nodes.add((obj, "file"))

            ##edge creation:
            label = format_my_nanos(eventEndTime)
            if operation == 'read' or operation == 'readv' or operation == 'recvmsg' or operation == 'recvfrom':
                edges.append(dict(x=obj, y=finalProcessName, label=label))
            else:
                edges.append(dict(x=finalProcessName, y=obj, label=label))

        i = i + 1

    graphGenerator(nodes, edges)


def format_my_nanos(nanos):
    dt = datetime.fromtimestamp(nanos / 1e9)
    # '%Y-%m-%dT%H:%M:%S.%f'
    return '{}{:03.0f}'.format(dt.strftime('%H:%M:%S.%f'), nanos % 1e3)


def processSubjectName(each):
    processID = each[4].replace('(', '').replace(')', '')
    processName = each[3]
    finalProcessName = processID + "_" + processName
    return finalProcessName


def extractLineContents(fileName):
    with open(fileName, 'r') as f:
        linesList = []
        for line_num, line in enumerate(f):
            # split contents of each line:
            eachLineContents = line.split('<#_#>')
            linesList.append(eachLineContents)
    return linesList


if __name__ == '__main__':
    # fileName = input("Enter the file name:\n")
    parseTextFile("output1.txt")
    # graphGenerator()
