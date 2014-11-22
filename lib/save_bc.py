import requests
import json
import time

serverURL = 'http://localhost:18081/save_bc'

headers = {'content-type': 'application/json'}

# payload = json.dumps({
#     "jsonrpc": "2.0",
#     "id": "test",
#     "method": "save_bc"
# })


def save_bc():
    #resp = requests.get(serverURL, headers=headers, data=payload)
    resp = requests.get(serverURL)
    # try:
    #     output = json.loads(resp.text)
    #     print output
    # except:
    #     print "Waiting for bitmonerod client to sync with network..."
    #     output = "Waiting for bitmonerod client to sync with network..."

    print resp.text