import requests
import json
import time

serverURL = 'http://localhost:19091/json_rpc'
headers = {'content-type': 'application/json'}
payload1 = json.dumps({
"jsonrpc": "2.0",
"method": "getbalance",
"params": {}
})
payload2 = json.dumps({
"jsonrpc": "2.0",
"method": "getaddress",
"params": {}
})

def balancecheck(jobqueue, resultsqueue):
    """function to make rpc call to simplewallet to get current balance"""
    kivysignal = True
    while kivysignal:
        time.sleep(2)
        walletrunning, kivysignal = jobqueue.get()
        if walletrunning:
            #print 'attempting rpc call'
            try:
                #Make rpc call
                resp1 = requests.get(serverURL, headers=headers, data=payload1)
                output1 = json.loads(resp1.text)

                #Parse json data to get balance info
                rawbalance = str(output1[u'result'][u'balance']/1e12)
                rawunlockedbalance = str(output1[u'result'][u'unlocked_balance']/1e12)

                #Format data for kivy
                balance = '[color=00ff00]'+rawbalance+'[/color]'
                unlockedbalance = '[color=00ff00]'+rawunlockedbalance+'[/color]'

                resp2 = requests.get(serverURL, headers=headers, data=payload2)
                output2 = json.loads(resp2.text)
                address = str(output2[u'result'][u'address'])

            except:
                #Return out of sync if bitmonerod is not ready
                balance = '[color=ff0000]out of sync[/color]'
                unlockedbalance = '[color=ff0000]out of sync[/color]'
                address = '[color=ff0000]out of sync[/color]'

            resultsqueue.put((balance, unlockedbalance, address))
