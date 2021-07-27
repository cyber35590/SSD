import hashlib
import os
import shutil

from backend import scheduler
from common.error import *
from common.utils import mkdir_rec, join
from django.core.files.uploadhandler import FileUploadHandler
from django.http import HttpRequest

from .config import config, log
from common.backup_request import BackupRequest
from common import utils
from .models import Backup, abs_backup, Node, Value

from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class NodeManager:



    def exists(self, url):
        if not url[-1] == "/":  url += "/"
        return len(Node.objects.filter(url__exact=url))

    def get(self, url):
        if not url[-1] == "/":  url += "/"
        ret = Node.objects.filter(url__exact=url)
        if(len(ret)>0):
            assert(len(ret)==1)
            return ret[0]
        return None

    def update(self, url = None, force = True):
        if url is None:
            for node in Node.objects.all():
                node.update(force)
        elif isinstance(url, (list, tuple)):
            for u in url:
                self.update(u, force)
        elif isinstance(url, str):
            if not url[-1]=="/":  url+="/"
            node = self.get(url)
            if node is None:
                node = Node(url=url)
            node.update(force)
        raise SSD_BadParameterType()


class Server:
    _INSTANCE = None

    @staticmethod
    def get_instance():
        if Server._INSTANCE is None:
            Server._INSTANCE = Server()
        return Server._INSTANCE


    def __getitem__(self, item):
        val = Value.objects.filter(key__exact=item)
        if len(val)==0: return None
        assert(len(val)==1)
        val=val[0]
        return val.get()

    def __setitem__(self, item, value):
        val = Value.objects.filter(key__exact=item)
        if len(val)==0:
            val = Value()
        else:
            val=val[0]
        return val.set(value)

    def __contains__(self, item):
        val = Value.objects.filter(key__exact=item)
        if len(val) == 0: return None
        return True

    def __init__(self):
        self.nodes=NodeManager()
        self.forward=[]
        self.fallback=[]
        self.url=None

        for section in config.sections():
            for opt in config.options(section):
                key = "config.%s.%s" % (section, opt)
                val = config[section, opt]
                self[key]=val

        allnodes=( self["config.nodes.forward"] or []) + \
                    (self["config.nodes.fallback"] or [])\
                    (self["config.nodes.other"] or [])

        #self.nodes.update(allnodes)
        #self.nodes.update() # si il y a d'autres noeud qui ne sont pas dans la config





    def handle_backup_request(self, data : dict , isForward : bool = False):
        assert isinstance(data, dict)
        bcr = BackupRequest(data)
        log.info("Requête de sauvegarde pour %s.%s taille %s" % (bcr.agent,bcr.backup_name, format_size(bcr.size)))

        du = shutil.disk_usage(config.get_backup_dir())
        left_after = du.total - du.used - bcr.size
        thresold = 0.05 * du.total

        if left_after < thresold:
            missing = thresold - left_after
            log.error("Impossible d'effectuer la sauvegarde de %s.%s, %s d'espace de stockage manquant" %
                      (bcr.agent,bcr.backup_name, format_size(missing)))
            return SSDE_NoFreeSpace(missing)

        if Backup.exists(bcr.backup_hash()):
            log.debug("La requête de sauvegarde a déjà été traitée")
            return SSDE_RessourceExists("Le backup '%s' existe déja" % bcr.hash)

        backup = Backup.from_request(bcr)
        log.info("La sauvegarde de %s.%s (%s) est autorisée" %(bcr.agent,bcr.backup_name, format_size(bcr.size)))
        return SSDE_OK({
            "token": backup.request_token
        })



    def handle_backup(self, req : HttpRequest):
        log.debug("Envoi de sauvegarde")
        if not "X-upload-token" in req.headers:
            log.error("L'envoi de sauvegarde ne possède pas de token")
            return SSDE_MalformedRequest("L'entête 'X-upload-token' n'est pas passée dans la requête", ["X-upload-token"])
        token = req.headers["X-upload-token"]

        backup = Backup.from_token(token)
        if not backup:
            log.error("Le token demandé (%s) ne correspond à aucune requête de sauvegarde connu" % token)
            raise SSDE_NotFound("La sauvegarde lié au token '%s' n'existe pas" % token, (token,))

        if backup.is_complete():
            log.warn("Le token demandé (%s) a déja été traité" % token)
            raise SSDE_RessourceExists("La sauvegarde lié au token '%s' n'existe pas" % token)

        log.info("Traitement de l'envoi de sauvegarde de %s.%s (%s)" %
                 (backup.agent,backup.backup_name, format_size(backup.size)))
        
        path = backup.path
        mkdir_rec(join(path, ".."))
        ifd = req.FILES["archive"]
        with open(path, "wb") as ofd:
            hash_sha = hashlib.sha3_512()
            for chunk in ifd.chunks():
                ofd.write(chunk)
                hash_sha.update(chunk)

        calculated_hash = hash_sha.hexdigest()
        if calculated_hash != backup.hash:
            log.error("Erreur les codes de hachage ne correspondent pas (attendu: '%s', calculé: '%s'"%
                      (backup.hash, calculated_hash))
            return SSDE_CorruptedData("Le code de hachage ne correspond pas", [backup.hash, calculated_hash])

        backup.complete()
        log.info("La sauvegarde a été correctement traité")
        if backup.forward_left is None: #None -> on transmet à tout le monde
            pass #todo
        else:
            scheduler.forward_backup(backup)

        return SSDE_OK()

def init():
    Server.get_instance()
    exit(0)