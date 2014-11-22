import requests
import json

serverURL = 'http://localhost:8082/json_rpc'


def CheckBalanceSimplewallet():
    """function to make rpc call to simplewallet to get current balance"""
    payload = json.dumps({
    "jsonrpc": "2.0",
    "method": "getbalance",
    "params": {}
    })
    print 'Attempting {0} RPC call'.format(CheckBalanceSimplewallet.__name__)
    try:
        #Make rpc call
        headers = {'content-type': 'application/json'}
        resp = requests.get(serverURL, headers=headers, data=payload)
        output = json.loads(resp.text)

        #Parse json data to get balance info
        balance = str(output[u'result'][u'balance']/1e12)
        unlockedbalance = str(output[u'result'][u'unlocked_balance']/1e12)

        return output, balance, unlockedbalance


    except:
        #Return out of sync if bitmonerod is not ready
        message = "Can't connect to simplewallet"
        return message, message, message



if __name__ == "__main__":
    print CheckBalanceSimplewallet()