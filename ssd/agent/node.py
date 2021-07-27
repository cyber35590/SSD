import json
import time

import requests
from common.error import *
from agent.config import log

class Node:
    RATE_BODY_LENGTH=1024*256
    def __init__(self, url):
        self.url = url if url[-1]=="/" else (url+"/")

        #info
        self.name = None
        self.ping = None # ping en s
        self.rate = None # débit en o/s

    def get(self, url, *args, **kwargs):
        res = requests.get(self.url+url, *args, **kwargs)
        return SSDError.from_json(res.content)

    def post(self, url, *args, **kwargs):
        res = requests.post(self.url+url, *args, **kwargs)
        return SSDError.from_json(res.content)

    def get_infos(self):
        res = self.get(self.url+"backend/infos")
        if res.ok():
            return res.data
        else:
            log.error("impossible de récupérer les infos de '%s'. Raison : '%s' (%d)"%(
                self.url, res.message, res.code
            ))
            return None

    def ping(self):
        t1 = time.time()
        res = self.get(self.url+"backend/ping")
        t =  time.time() - t1
        if res.ok():
            self.ping = t
        else:
            self.ping = None
        return self.ping

    def rate(self):
        t1 = time.time()
        res = self.post(self.url+"backend/ping", "0"*Node.RATE_BODY_LENGTH)
        t = time.time()
        if res.ok():
            self.rate = (time.time() - t1)/Node.RATE_BODY_LENGTH
        else:
            self.rate = None
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
