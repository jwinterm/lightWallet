import requests
import json

serverURL = 'http://localhost:8082/json_rpc'

payload = json.dumps({
    "jsonrpc": "2.0",
    "method": "store",
    "params": {}
})


def checkwalletrpccall():
    headers = {'content-type': 'application/json'}
    resp = requests.get(serverURL, headers=headers, data=payload)
    output = json.loads(resp.text)
    print output

#    return output[u'result'][u'balance'], output[u'result'][u'unlocked_balance']

if __name__ == "__main__":
    checkwallet()