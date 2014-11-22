import os
import time

def namecheck(jobqueue, resultsqueue):
    kivysignal = True
    while kivysignal:
        try:
            walletname, kivysignal = jobqueue.get()
            # print walletname
            if walletname == "No filename":
                message = "Please input a wallet file name..."
                isname = None
            elif os.path.isfile(walletname):
                message = "Wallet file {0} exists in local directory.\nPlease press [b]Initialize wallet file[/b] to [color=00ff00]load wallet file[/color].".format(walletname)
                isname = True
            if not os.path.isfile(walletname):
                message = "Wallet file {0} does not exist in your local directory.\nPlease press [b]Initialize wallet file[/b] to [color=00ff00]generate new wallet file[/color].".format(walletname)
                isname = False
            resultsqueue.put((isname, message))
        except:
            pass
        time.sleep(0.1)