"""
[nom de l'entrée]
path = ["/homme/commone", "/opt/app"]
node = "https://uneurl:8000/"
backup_dir = "."
fallback = ["https://url1:8000", "https://url2:8000/"]
"""
import datetime
import os
import time

from agent.archive import make_archive
from common.backup_request import BackupRequest

from .config import log, config
from common.error import *
from .node import Node

DEFAULT_ENTRY_PARAM = {
    "name" : "unnamed",
    "path" : None,
    "node" : None,
    "temp_dir" : "temp",
    "fallback" : None
}

def get_opt(entry, name=None) :
    if name:
        try:
            return config[entry, name]
        except KeyError:
            pass

        try:
            return config["global", name]
        except KeyError:
            pass

        if DEFAULT_ENTRY_PARAM[name] : return DEFAULT_ENTRY_PARAM[name]
    else:
        try:
            return config["global", entry]
        except KeyError:
            pass

    raise SSD_ConfigMissingParam("Erreur dans l'entrée '%s' le paramètre '%s' n'est pas défini"%(entry, name))

class Entry:

    @staticmethod
    def from_config(entry : str):
        return  Entry({
            "name": entry,
            "files": get_opt(entry, "files"),
            "node": get_opt(entry, "node"),
            "agent_url" : get_opt("url"),
            "temp_dir": get_opt(entry, "temp"),
            "fallback": get_opt(entry, "fallback"),
            "forward": get_opt(entry, "forward")
        })

    def __init__(self, data : dict):
        self.name = data["name"]
        self.dirs = data["files"]
        self.agent_url = data["agent_url"]
        self.current_node = None
        node = data["node"]
        fallback = data["fallback"] if data["fallback"] else []
        self.temp_dir = data["backup_dir"] if "backup_dir" in data else "temp"
        self.forward = data["forward"] if "forward" in data else None
        if isinstance(self.forward, str) : self.forward = [self.forward]
        self.nodes = list(map(lambda  x: Node(x), [node] + fallback))

    def create_archive(self):
        log.info("Créeation de l'archive pour l'entrée de sauvegarde '%s'")
        path, hash= make_archive(self.temp_dir, self.dirs)
        log.debug("Fichier: %s" % path)
        return path, hash


    def find_node_by_url(self, url : str) -> (Node, None):
        assert(isinstance(url, str))
        if url[-1]!='/': url+="/"
        for node in self.nodes:
            if node.url==url:
                return node
        return None

    def get_token(self, path : str, hash : str) -> SSDError :
        assert(isinstance(path, str))
        assert(isinstance(hash, str))
        assert(os.path.isfile(path))
        self.current_node = None
        size = os.path.getsize(path)
        data = {
            "time" : time.time(),
            "agent" : config["global", "site"],
            "from" : "Agent/"+config["global", "site"],
            "size" : size,
            "hash" : hash,
            "backup_name" : self.name,
            "agent_url" : self.agent_url,
            "forward" : self.forward
        }

        log.info("Requête de sauvegarde de %s.%s (%s)" % (config["global", "site"], self.name, format_size(size)))
        for node in self.nodes:
            log.debug("Demande à '%s'" % (node.url))
            ret = node.request_backup(data)
            if ret.ok():
                self.current_node = node
                log.debug("Sauvegarde autorisée sur '%s'"%node.url)
                return ret
            log.debug("Sauvegarde impossible sur '%s', raison: '%s'"%(node.url, ret.message))
        log.critical("Erreur impossible de faire la sauvegarde, aucun noeud n'a pu répondre à la requête")
        return SSDE_NoNodeAvailable()

    def upload(self, file : str, token : str) -> SSDError:
        assert(isinstance(file, str))
        assert(os.path.isfile(file))
        assert(isinstance(file, str))

        ret = self.current_node.upload(file, token)
        if ret.err():  return ret
        self.current_node=None
        return ret

    def backup(self) -> SSDError:
        path, hash = self.create_archive()
        res = self.get_token(path, hash)

        if not self.current_node or res.err(): return res

        token = res["token"]
        res = self.upload(path, token)

        os.remove(path)
        return res