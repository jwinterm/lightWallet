from subprocess import PIPE, Popen
from threading  import Thread
from Queue import Queue, Empty

def bitmonerodloader():
    """Start bitmonerod and/or simplewallet and collect wallet name and address"""
    p = Popen(
    # ["bitmonerod.exe", "--set_log", "0"],
    ["bitmonerod.exe", "--set_log", "0"],
    stdout=PIPE,
    stdin=PIPE,
    bufsize=1,
    close_fds=ON_POSIX)



