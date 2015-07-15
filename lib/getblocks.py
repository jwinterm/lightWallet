import requests
import json
import time
import datetime
import ctypes


pyarr = [1]
arr = (ctypes.c_int * len(pyarr))(*pyarr)
# Set server for RPC call to bitmonerod
default_URL = 'http://localhost:18081/gettransactions'
# Headers, because headers
headers = {'content-type': 'application/json'}
# Data to give to bitmonerod to check last block info
payload = json.dumps({'tx ids': '<b2a4cd9823ae3c0044646115d344931e1e15f4ccb68879a00f11b9672599b0a1>'})


def GetBlocks(serverURL=default_URL):
    """Try and get last block info and return formatted text"""
    # print('Attempting {0} RPC call'.format(CheckLastBlock.__name__))
    try:
        resp = requests.get(serverURL, headers=headers, data=payload)
        # output = json.loads(resp.text)
        print(resp)


    except:
        #Return out of sync if bitmonerod is not ready
        message = "Can't connect to bitmonerod"
        return message, message, message, message


if __name__ == "__main__":
   GetBlocks()