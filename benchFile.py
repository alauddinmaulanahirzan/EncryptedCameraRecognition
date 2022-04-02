import psutil
import time
import sys
import os

## Benchmark Functions

def getMillis():
    milliseconds = int(round(time.time() * 1000))
    return milliseconds

def getCPUPercent(process):
    os = sys.platform
    if(os == "linux"):
        cpu_per = process.cpu_percent() / psutil.cpu_count()
    else:
        cpu_per = process.cpu_percent()
    return cpu_per

def getMemData(process):
    memData = process.memory_full_info().data
    return float(memData/(1024*1024))

def getMemUSS(process):
    memUSS = process.memory_full_info().uss
    return float(memUSS/(1024*1024))

## Logging ##

def writeFile(name,row):
    textfile = open(name+".csv", "a")
    a = textfile.write(row)
    textfile.close()

def createFile(name):
    textfile = open(name+".csv", "w")
    header = '"Fungsi";"Millis";"CPU";"Mem";"USS"\n'
    a = textfile.write(header)
    textfile.close()

## Get Benchmark

def writeBenchmark(process,name,funct):
    millis = getMillis()
    cpu = getCPUPercent(process)
    mem = getMemData(process)
    uss = getMemUSS(process)
    row = '"{}";"{}";"{}";"{}";"{}"\n'.format(funct,millis,cpu,mem,uss)
    writeFile(name,row)

## Main Test

def main():
    pid = os.getpid()
    process = psutil.Process(pid)
    createFile("Test")
    getBenchmark(process,"Test","Funct")

if __name__ == '__main__':
    main()
