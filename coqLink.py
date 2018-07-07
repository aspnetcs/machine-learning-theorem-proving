from threading import Thread
from queue import Queue, Empty
from subprocess import Popen, PIPE
from time import sleep

class NonBlockingStreamReader:

    def __init__(self, stream):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()

        def _populateQueue(stream, queue):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''

            while True:
                line = stream.readline()
                if line:
                    queue.put(line)
                else:
                    return
                    #raise UnexpectedEndOfStream

        self._t = Thread(target = _populateQueue,
                args = (self._s, self._q))
        self._t.daemon = True
        self._t.start() #start collecting lines from the stream

    def readline(self, timeout = None):
        try:
            return self._q.get(block = timeout is not None,
                    timeout = timeout)
        except Empty:
            return None

class UnexpectedEndOfStream(Exception): pass

def output_from_command(process, nbsr, command=None):
    if command:
        command = command.encode()
        process.stdin.write(command)
        process.stdin.flush()
    outputList = []
    
    while True:
        output = nbsr.readline(0.1) # 0.1 secs to let the shell output the result
        if not output:
            outputList.append('No more data\n\n')
            return outputList
        else:
            outputList.append(output)
            
            
def pretty(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent+1)
        elif isinstance(value, list):
            for i in value:
                print('\t' * (indent+1) + str(i))
        else:
            print('\t' * (indent+1) + str(value))

def findID(serapiString):
    start = serapiString.find("Added")
    end = serapiString.find("((")
    thisID = serapiString[start + 6:end]
    return thisID
    
    
def doAdd(coqString, resultDict, process, nbsr, debugList = []):
    
    if 10 in debugList:
        debugList = [0,1,2,3]
        
    commandExtended = '(Add () "%s")' % coqString
    
    if 0 in debugList:
        print("Add command: ")
        print(commandExtended)
        print()
        
    addResult = output_from_command(process, nbsr, command=commandExtended)[-3].decode('ASCII')
    
    if 1 in debugList:
        print("Add command result: ")
        print(addResult)
        print()
        
    thisID = findID(addResult)
    
    execCommand = '(Exec %s)' % thisID
    execResult = output_from_command(process, nbsr, execCommand)
    
    if 2 in debugList:
        print("Exec result: ")
        print(execResult)
        print()
    
    
    if sum([1 if "Error" in i.decode('ASCII') else 0 for i in execResult if type(i) == bytes]) > 0:
        print("Error...")
        cancelCommand = '(Cancel (%s))' % thisID
        cancelResult = output_from_command(process, nbsr, command=cancelCommand)
        print("Cancel result: ")
        print(cancelResult)
        return resultDict
    
    goalCommand = '(Query ((pp ((pp_format PpStr)))) Goals)'
    goalResult = output_from_command(process, nbsr, goalCommand)
    
    if 3 in debugList:
        print("Goal Query result: ")
        print(goalResult)
        print()
    
    if len(goalResult) == 1:
        result =  [(['none'],None)]
    else:
        result = goalResult[1].decode('ASCII').replace('\\n','\n')
    
    if '"' not in result or 'CoqString""' in result:
        result = [(['none'],None)]
    else:
        start = result.find('"')
        result = result[start + 1:]
        end = result.find('"')
        result = result[:end]

        goalList = result.strip().split("\n\n")

        result = [i.split('\n============================\n') for i in goalList]
        result = [(i[0].strip().split('\n'),i[1].replace('\n','')) for i in result]
        result = [([j.strip() for j in i[0]], " ".join(i[1].split())) for i in result]
    
    if coqString in resultDict.keys():
        resultDict[coqString + "     duplicate: " + str(np.random.randint(0,1000))] = result
    else:
        resultDict[coqString] = result
    return resultDict
    
def doCommand(command, process, nbsr, resultDict={}):
    if command in resultDict.keys():
        resultDict[command + "     duplicate: " + str(np.random.randint(0,1000))] = output_from_command(process, 
                                                                                                        nbsr, 
                                                                                                        command=command)
    else:
        resultDict[command] = output_from_command(process, nbsr, command=command)
    return resultDict
