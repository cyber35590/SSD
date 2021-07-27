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
        assert(isinstance(url, str))
        if len(url) and url[0]=='/':
            url=url[1:]
        url = self.url + url
        try:
            res = requests.get(url, *args, **kwargs)
        except requests.exceptions.ConnectionError as err:
            if isinstance(err.args[0], (Exception)):
                err = err.args[0]
            return SSDE_ConnectionError("Impossible de joindre le serveur (%s) : %s" %(url, err.reason), (url,))
        return SSDError.from_json(res.content)

    def post(self, url, *args, **kwargs):
        assert(isinstance(url, str))
        if len(url) and url[0]=='/':
            url=url[1:]
        url = self.url + url
        try:
            res = requests.post(url, *args, **kwargs)
        except requests.exceptions.ConnectionError as err:
            if isinstance(err.args[0], (Exception)):
                err = err.args[0]
            return SSDE_ConnectionError("Impossible de joindre le serveur (%s) : %s" %(url, err.reason), (url,))
        return SSDError.from_json(res.content)

    def get_infos(self):
        res = self.get("/node/infos")
        if res.ok():
            return res.data
        else:
            log.error("impossible de récupérer les infos de '%s'. Raison : '%s' (%d)"%(
                self.url, res.message, res.code
            ))
            return None

    def ping(self):
        t1 = time.time()
        res = self.get("/node/ping")
        t =  time.time() - t1
        if res.ok():
            self.ping = t
        else:
            self.ping = None
        return self.ping

    def rate(self):
        t1 = time.time()
        res = self.post("/node/ping", "0"*Node.RATE_BODY_LENGTH)
        t = time.time()
        if res.ok():
            self.rate = (time.time() - t1)/Node.RATE_BODY_LENGTH
        else:
            self.rate = None
        return self.rate


    def request_backup(self, meta):
        metastr = json.dumps(meta)
        return self.post("/node/backup/request", data=metastr)

    def upload(self, file : str, token : str):
        headers = {
            "X-upload-token": token
        }
        files = {
            "archive": open(file, "rb")
        }
        return self.post("/node/backup", files=files, headers=headers)

            #Todo
        #Todo
