import json
import time

import requests
from common.error import *


class Node:
    RATE_BODY_LENGTH=1024*256
    def __init__(self, url):
        self.url = url if url[-1]=="/" else (url+"/")

        #info
        self.name = None
        self.ping = None # ping en s
        self.rate = None # débit en o/s

    def get_info(self):
        #Todo
        pass

    def ping(self):
        t1 = time.time()
        res = requests.get(self.url+"ping")
        self.ping = time.time() - t1
        return self.ping

    def rate(self):
        t1 = time.time()
        res = requests.post(self.url+"ping", "0"*Node.RATE_BODY_LENGTH)
        t = time.time()
        self.rate = (time.time() - t1)/Node.RATE_BODY_LENGTH
        return self.rate


    def request_backup(self, meta):
        metastr = json.dumps(meta)
        res = requests.post(self.url + "node/backup/request", data=metastr)
        return SSDError.from_json(res.content)

    def upload(self, file : str, token : str):
        headers = {
            "X-upload-token": token
        }
        files = {
            "archive": open(file, "rb")
        }
        res = requests.post(self.url + "node/backup", files=files, headers=headers)
        return SSDError.from_json(res.content)

            #Todo
        #Todo
