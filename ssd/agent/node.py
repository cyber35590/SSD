import json
import os.path
import time

import requests
from common.error import *
from agent.config import log
from common import utils

class Node:
    RATE_BODY_LENGTH=1024*256
    def __init__(self, url):
        self.url = url if url[-1]=="/" else (url+"/")

        #info
        self.name = None
        self.ping = None # ping en s
        self.rate = None # débit en o/s

    def get(self, url, *args, **kwargs) -> SSDError:
        assert(isinstance(url, str))
        if len(url) and url[0]=='/':
            url=url[1:]
        url = self.url + url
        return utils.get(url, *args, **kwargs)

    def post(self, url, *args, **kwargs) -> SSDError:
        assert(isinstance(url, str))
        if len(url) and url[0]=='/':
            url=url[1:]
        url = self.url + url
        return utils.post(url, *args, **kwargs)

    def get_infos(self) -> dict:
        res = self.get("/node/infos")
        if res.ok():
            return res.data
        else:
            log.error("impossible de récupérer les infos de '%s'. Raison : '%s' (%d)"%(
                self.url, res.message, res.code
            ))
            return None

    def ping(self) -> float:
        t1 = time.time()
        res = self.get("/node/ping")
        t =  time.time() - t1
        if res.ok():
            self.ping = t
        else:
            self.ping = None
        return self.ping

    def rate(self) -> float:
        t1 = time.time()
        res = self.post("/node/ping", "0"*Node.RATE_BODY_LENGTH)
        t = time.time()
        if res.ok():
            self.rate = (time.time() - t1)/Node.RATE_BODY_LENGTH
        else:
            self.rate = None
        return self.rate


    def request_backup(self, meta : dict) -> SSDError:
        metastr = json.dumps(meta)
        return self.post("/node/backup/request", data=metastr)

    def upload(self, file : str, token : str) -> SSDError:
        assert(isinstance(file, str))
        assert(os.path.isfile(file))
        assert(isinstance(token, str))
        headers = {
            "X-upload-token": token
        }
        files = {
            "archive": open(file, "rb")
        }
        return self.post("/node/backup", files=files, headers=headers)
