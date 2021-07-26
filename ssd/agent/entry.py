"""
[nom de l'entrée]
path = ["/homme/commone", "/opt/app"]
node = "https://uneurl:8000/"
backup_dir = "."
fallback = ["https://url1:8000", "https://url2:8000/"]
"""
import os
import time

from agent.archive import make_archive
from .config import log, config
from common.error import SSD_ConfigMissingParam
from .node import Node

DEFAULT_ENTRY_PARAM = {
    "name" : "unnamed",
    "path" : None,
    "node" : None,
    "temp_dir" : "temp",
    "fallback" : None
}

def get_opt(entry, name):
    try:
        return config[entry, name]
    except:
        pass

    try:
        return config["global", name]
    except:
        pass

    if DEFAULT_ENTRY_PARAM[name] : return DEFAULT_ENTRY_PARAM[name]

    raise SSD_ConfigMissingParam("Erreur dans l'entrée '%s' le paramètre '%s' n'est pas défini"%(entry, name))

class Entry:

    @staticmethod
    def from_config(entry):
        return  Entry({
            "name": get_opt(entry, "name"),
            "path": get_opt(entry, "path"),
            "node": get_opt(entry, "node"),
            "temp_dir": get_opt(entry, "temp_dir"),
            "fallback": get_opt(entry, "fallback")
        })

    def __init__(self, data : dict):
        self.name = data["name"]
        self.dirs = data["path"]
        node = data["node"]
        fallback = data["fallback"] if data["fallback"] else []
        self.temp_dir = data["backup_dir"] if "backup_dir" in data else "temp"

        self.nodes = list(map(lambda  x: Node(x), [node] + fallback))

    def create_archive(self):
        log.info("Créeation de l'archive pour l'entrée de sauvegarde '%s'")
        path, hash= make_archive(self.temp_dir, self.dirs)
        log.debug("Fichier: %s" % path)
        return path, hash


    def get_token(self, path, hash):
        size = os.path.getsize(path)
        data = {
            "time" : time.time(),
            "agent" : config["global", "site"],
            "from" : "Agent/"+config["global", "site"],
            "size" : size,
            "hash" : hash
        }

        log.info("Requête de sauvegarde")
        for node in self.nodes:
            log.debug("Demande à '%s'" % str(node))
            allowed = node.request_backup(data)
            if allowed:
                log.debug("\tSauvegarde autorisée")
                return True
            log.debug("\tSauvegarde impossible")
        log.critical("Erreur impossible de faire la sauvegarde, aucun noeud n'a pu répondre à la requête")
        return False

    def upload(self, file, res):


        return res

    def backup(self):
        path, hash = self.create_archive()
        res = self.get_token(path, hash)
        res = self.upload(path, res)
        os.remove(path)