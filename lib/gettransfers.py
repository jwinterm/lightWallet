import requests
import json
import time

serverURL = 'http://localhost:19091/json_rpc'

headers = {'content-type': 'application/json'}

payload = json.dumps({
    "jsonrpc": "2.0",
    "method": "incoming_transfers",
    "params": {"transfer_type": "all"}
})

# payload = json.dumps({
#     "jsonrpc": "2.0",
#     "method": "incoming_transfers",
#     "params": {"transfer_type": "all"}
# })


def getTransfers():
    unspent_txs, spent_txs = [], []
    try:
        resp = requests.get(serverURL, headers=headers, data=payload)
        output = json.loads(resp.text)
        for i in output[u'result'][u'transfers']:
            if i[u'spent'] == False:
                unspent_txs.append([i[u'tx_hash'].strip('<>'), int(i[u'amount'])/1e12, i[u'spent']])
            elif i[u'spent'] == True:
                spent_txs.append([i[u'tx_hash'].strip('<>'), int(i[u'amount'])/1e12, i[u'spent']])
    except:
        pass
    return unspent_txs, spent_txs


if __name__ == '__main__':
    getTransfers()