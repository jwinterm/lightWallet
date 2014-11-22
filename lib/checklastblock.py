import requests
import json
import time
import datetime


# Set server for RPC call to bitmonerod
default_URL = 'http://xmr1.coolmining.club:5012/json_rpc'
# Headers, because headers
headers = {'content-type': 'application/json'}
# Data to give to bitmonerod to check last block info
payload = json.dumps({
    "jsonrpc": "2.0",
    "id": "test",
    "method": "getlastblockheader"
})


def CheckLastBlock(serverURL=default_URL):
    """Try and get last block info and return formatted text"""
    # print('Attempting {0} RPC call'.format(CheckLastBlock.__name__))
    try:
        resp = requests.get(serverURL, headers=headers, data=payload)
        output = json.loads(resp.text)
        # print(output)
        height = output[u'result'][u'block_header'][u'height']
        reward = output[u'result'][u'block_header'][u'reward']
        linuxblocktime = output[u'result'][u'block_header'][u'timestamp']
        linuxtimenow = time.time()
        timesince = linuxtimenow - linuxblocktime
        localtime = datetime.datetime.fromtimestamp(int(linuxblocktime
            )).strftime('%Y-%m-%d %H:%M:%S')
        return height, reward, timesince, localtime


    except:
        #Return out of sync if bitmonerod is not ready
        message = "Can't connect to bitmonerod"
        return message, message, message, message


if __name__ == "__main__":
   CheckLastBlock()