#!/usr/bin/python
from sys import platform
import subprocess as sub
import time
from lib.checklastblock import CheckLastBlock


def runningcheck():
    """Function to check if daemon is running"""
    daemonrunning = False
    if platform == 'win32':
        import wmi
        wmi = wmi.WMI ()
        for process in wmi.Win32_Process(name='bitmonerod.exe'):
            #print process.ProcessId, process.Name
            if process.Name:
                daemonrunning = True

    elif platform == 'linux' or platform == 'linux2' or platform == 'linux32':
        p = sub.Popen("ps -A | grep bitmonerod", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
        output, errors = p.communicate()
        if output:
            daemonrunning = True
    return daemonrunning

def daemoncheck(queue):
    """Check if bitmonerod daemon is running and return values to kivy"""
    print "Starting checkdaemon thread on: {0}".format(platform)

    while True:
        daemonrunning = runningcheck()
        if daemonrunning:
            try:
                checklastblockoutput = CheckLastBlock()

            except:
                checklastblockoutput = 'error'
        else:
            checklastblockoutput = 'daemon not running'
        queue.put((daemonrunning, checklastblockoutput))
        time.sleep(1)



if __name__ == '__main__':
    daemoncheck()