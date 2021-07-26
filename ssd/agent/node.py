import json

import requests


class Node:
    def __init__(self, url):
        self.url = url if url[-1]=="/" else (url+"/")
        #state
        self.last_token = None
        self.update_allowed = False

        #info
        self.name = None
        self.ping = None # ping en s
        self.rate = None # débit en o/s

    def get_info(self):
        #Todo
        pass

    def ping(self):
        #Todo
        pass

    def rate(self):
        #Todo
        pass

    def request_backup(self, meta):
        metastr = json.dumps(meta)
        res = requests.post(self.url + "node/backup/request", data=metastr)
        if res.status_code < 400:
            resjoson = json.loads(res.content)
            # {
            #    "url" : URL_TO_UPDTE
            #    "token": XXXXXXXXX
            # }
            self.update_allowed = False
            self.last_token = resjoson["token"]
            return True
        return False

    def update(self, file):
        if self.update_allowed:
            headers = {
                "X-upload-token": self.last_token
            }
            files = {
                "archive": open(file, "rb")
            }
            res = requests.post(self.url + "node/backup", files=files, headers=headers)


            self.update_allowed = False
            self.last_token = None


            #Todo
        #Todo
