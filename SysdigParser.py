from graphviz import Digraph
from datetime import datetime
from collections import deque

import re


def graphVizGenerator(nodes, edges):
    g = Digraph('G', filename='graph.gv', format='svg')

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


def generateGraph(edgesList):
    ##Node Addition:
    nodes = set()
    edges = []
    for each in edgesList:
        #print("Each Edge:" + str(each))
        nodes.add((each['u'], each['uType']))
        nodes.add((each['v'], each['vType']))
        label = "[" + format_my_nanos(each['startTime']) + ", " + format_my_nanos(each['endTime']) + "]"
        edges.append(dict(x=each['u'], y=each['v'], label=label))

    graphVizGenerator(nodes, edges)


def parseTextFile(fileName):
    lineContents = extractLineContents(fileName)
    i = 0

    # filter out exit events only:
    allEdgesList = list()
    for each in lineContents:
        # if line contents are not empty
        if len(each) > 0 and each[5] == '<':
            #print(each)
            # extracting information:
            finalProcessName = processSubjectName(each)
            operation = each[6]
            obj = each[9].replace('fdName=', '').replace(":", " port ").replace("->", "=>")
            eventEndTime = int(each[1])
            latency = int(each[10].replace('latency=', ''))
            eventStartTime = eventEndTime - latency
            fdType = each[8].replace('fdtype=', '')

            if len(obj) == 0:
                continue

            ##Constructing each edge data
            ##edge creation
            eachEvent = createEvent(eventEndTime, eventStartTime, fdType, finalProcessName, latency, obj, operation)
            allEdgesList.append(eachEvent)

        i = i + 1

    return allEdgesList


def createEvent(eventEndTime, eventStartTime, fdType, finalProcessName, latency, obj, operation):
    u, uType, v, vType = findUandV(fdType, finalProcessName, obj, operation)
    eachEvent = dict(u=u, v=v, operation=operation,
                     startTime=eventStartTime, endTime=eventEndTime,
                     latency=latency, uType=uType, vType=vType)
    return eachEvent


def findUandV(fdType, finalProcessName, obj, operation):
    u = finalProcessName
    v = obj
    uType = 'process'
    vType = 'file'
    if fdType == 'ipv4' or fdType == 'ipv6':
        vType = 'ip'
    if operation == 'read' or operation == 'readv' or operation == 'recvmsg' or operation == 'recvfrom':
        u = obj
        v = finalProcessName

        temp = uType
        uType = vType
        vType = temp
    return u, uType, v, vType


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


def processBackTracking(reverseMapOfEdges, queue):
    resultList = []
    i = 0
    while len(queue) > 0:
        i = i+1
        item = queue.popleft()
        maxEndTime = item.get('maxEndTime')
        node = item.get('node')

        print(f"Back Track level : {i}")
        if reverseMapOfEdges.get(node) is not None:
            sourceNodes = reverseMapOfEdges.get(node)

            for eachSourceNode in sourceNodes:
                edges = sourceNodes.get(eachSourceNode)
                if len(edges) > 0:
                    filteredList = list(filter(lambda d: d['startTime'] < maxEndTime, edges))
                    if len(filteredList) > 0:
                        resultList.extend(filteredList)
                        maxEndTimeForThisSource = getMaxEndTime(filteredList)
                        maxEndTimeForThisSource = min(maxEndTimeForThisSource, maxEndTime)
                        pushToQueue(queue, eachSourceNode, maxEndTimeForThisSource)

    return resultList


def processBackTrackingBySourceDestination(edgesList, source, dist):
    filteredEdges = []
    reverseMapOfEdges = generateReverseMapOfEdges(edgesList)

    if reverseMapOfEdges.get(dist) is not None:
        entryNodes = reverseMapOfEdges.get(dist)
        if entryNodes.get(source) is not None:
            edges = entryNodes.get(source)

            if len(edges) > 0:
                filteredEdges.extend(edges)
                maxEndTime = getMaxEndTime(edges)
                print(maxEndTime)
                # insertIntoqueue:
                queue = deque()
                pushToQueue(queue, source, maxEndTime)

                ##backtracking based on queue:
                filteredEdges.extend(processBackTracking(reverseMapOfEdges, queue))

        else:
            print(f"Mentioned Source Node not found -> {source}")

    else:
        print(f"Mentioned Destination Node not found -> {dist}")

    return filteredEdges


def pushToQueue(queue, source, maxEndTime):
    entry = dict(node=source, maxEndTime=maxEndTime)
    queue.append(entry)


def getMaxEndTime(edges):
    ##find max of all the new edges added:
    edges = sorted(edges, key=lambda e: e.get('endTime'), reverse=True)
    maxEdge = edges[0]
    maxEndTime = maxEdge.get('endTime')
    return maxEndTime


def generateReverseMapOfEdges(edgesList):
    reverseMapOfEdges = dict()
    for each in edgesList:
        u = each.get('u')
        v = each.get('v')
        entryNodes = reverseMapOfEdges.get(v, dict())
        edgesFromEachNode = entryNodes.get(u, [])
        edgesFromEachNode.append(each)
        entryNodes[u] = edgesFromEachNode
        reverseMapOfEdges[v] = entryNodes
    return reverseMapOfEdges


if __name__ == '__main__':
    fileName = input("Enter the file Name to be analysed:\n")
    allEdgesList = parseTextFile(fileName)

    option = input("Enter 1 for full graph\n"
          "2 for backtracking")

    if option == '2':
        u = input("Enter the source node\n")
        v = input("Enter the destination node\n")
        print(u, v)
        allEdgesList = processBackTrackingBySourceDestination(allEdgesList, u, v)

    generateGraph(allEdgesList)
