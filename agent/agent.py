import json

from common.config_base import log, config
from .archive import make_archive
import os
import time
import requests

#time.strftime("%Y_%m_%d-%H_%M_%S")

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

    def request_update(self, meta):
        res = requests.post(self.url + "node/backup/request")
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





class Agent:

    def __init__(self):
        self.base_url=config["nodes", "default_url"]
        self.fallback=config["nodes", "fallback_urls"]
        self._nodes_url = [self.base_url] + self.fallback
        self.nodes = list(map(lambda x: Node(x), self._nodes_url))
        self.temp_dir = config.get_temp_dir()
        self.backup_dir = config.get_backup_dirs()

    def _make_archive(self):
        return make_archive(self.temp_dir, self.backup_dir)


    def _get_token(self, path, hash):
        size = os.path.getsize(path)
        data = {
            "time" : time.time(),
            "agent" : config["info", "site"],
            "from" : "Agent/"+config["info", "site"],
            "size" : size,
            "hash" : hash
        }

        urls = [self.base_url] + self.fallback
        log.info("Requête de sauvegarde")
        for node in self.nodes:
            log.debug("Demande à '%s'" % str(node))
            allowed = node.request_update(data)
            if allowed:
                log.debug("\tSauvegarde autorisée")
                return True
            log.debug("\tSauvegarde impossible")
        log.critical("Erreur impossible de faire la sauvegarde, aucun noeud n'a pu répondre à la requête")
        return False


    def _upload(self, file, res):


        return res

    def backup(self):
        path, hash = self._make_archive()
        res = self._get_token(path, hash)
        res = self._upload(path, res)
        os.remove(path)




