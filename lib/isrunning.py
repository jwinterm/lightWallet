# !/usr/bin/python
from sys import platform
import subprocess
import time


def runningcheck():
    """Function to check if daemon is running"""
    daemonrunning, walletrunning, minerrunning = False, False, False
    if platform == 'win32':
        import wmi

        wmi = wmi.WMI()
        for process in wmi.Win32_Process():
            # print process.ProcessId, process.Name
            if process.Name == 'bitmonerod.exe':
                daemonrunning = True
                # print 'daemon'
            if process.Name == 'simplewallet.exe':
                walletrunning = True
                # print 'wallet'
            if process.Name == 'minerd.exe':
                minerrunning = True
                # print 'miner'
    elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
        p = subprocess.Popen("ps -A", shell=True, stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE)
        output, errors = p.communicate()
        if 'bitmonerod' in output:
            daemonrunning = True
        if 'simplewallet' in output:
            walletrunning = True
        if 'minerd' in output:
            minerrunning = True
    return daemonrunning, walletrunning, minerrunning


def isrunning(jobqueue, resultsqueue):
    """Check if bitmonerod daemon is running and return values to kivy"""
    print "Starting checkdaemon thread on: {0}".format(platform)
    kivysignal = True
    while kivysignal:
        try:
            daemonrunning, walletrunning, minerrunning = runningcheck()
            if daemonrunning:
                daemoncheckerlabeltext = "[color=00ff00]It appears the bitmonerod daemon is running.[/color]"
            else:
                daemoncheckerlabeltext = "[color=ff0000]Click the [b]Start network daemon[/b] button to load bitmonerod.[/color]"
            if walletrunning:
                walletcheckerlabeltext = "[color=00ff00]It appears the simplewallet daemon is running.[/color]"
            else:
                walletcheckerlabeltext = "[color=00ff00]Click the [b]Initialize wallet file[/b] button to load simplewallet.[/color]"
            resultsqueue.put((daemonrunning, daemoncheckerlabeltext, walletrunning,
                              walletcheckerlabeltext, minerrunning))
        except:
            pass
        time.sleep(0.1)
        kivysignal = jobqueue.get(kivysignal)
