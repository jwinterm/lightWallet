import requests
import json
import time

serverURL = 'http://localhost:19091/json_rpc'

headers = {'content-type': 'application/json'}

payload = json.dumps({
    "jsonrpc": "2.0",
    "method": "store",
    "params": {}
})


def storeWallet():
    resp = requests.get(serverURL, headers=headers, data=payload)
    try:
        output = json.loads(resp.text)
#        print output
    except:
#        print "Waiting for bitmonerod client to sync with network..."
        output = "Waiting for bitmonerod client to sync with network..."

#    print output
