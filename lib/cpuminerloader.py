import subprocess
from sys import platform


def cpuminerloader(minerurl, user, pw, threads):
    """Start cpuminer"""
    print "Start miner button pressed..."
    #Start cpuminer daemon if not running
    if platform == 'win32':
        daemonproc = subprocess.Popen("start minerd.exe -a cryptonight -o {0} -u {1} -p {2} -t {3}".format(
                                      minerurl, user, pw, threads), shell=True)
    elif platform == 'linux' or platform == 'linux2' or platform == 'linux32':
        print "linux!"
        daemonproc = subprocess.Popen('xterm -bg black -e "./minerd -a cryptonight -o {0} -u {1} -p {2} -t {3}"'.format(
                                      minerurl, user, pw, threads), shell=True)

