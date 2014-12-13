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
    try:
        resp = requests.get(serverURL, headers=headers, data=payload)
        output = json.loads(resp.text)
    except:
        output = "Waiting for bitmonerod client to sync with network..."
    # print(output)
    return output

if __name__ == "__main__":
    storeWallet()
