import hashlib
import os
import shutil

from common.utils import NoneType
from backend import scheduler
from common.error import *
from common.utils import mkdir_rec, join
from django.core.files.uploadhandler import FileUploadHandler
from django.http import HttpRequest

from .config import config, log
from common.backup_request import BackupRequest, ForwardRequest
from common import utils
from .models import Backup, abs_backup, Node, Value

from django import forms

class NodeManager:
    def exists(self, url : str) -> bool:
        assert(isinstance(url, str))
        if not url[-1] == "/":  url += "/"

        assert(len(Node.objects.filter(url__exact=url))<2)
        return len(Node.objects.filter(url__exact=url))==1

    def get(self, url : str) -> (Node, None):
        assert(isinstance(url, str))
        if not url[-1] == "/":  url += "/"
        ret = Node.objects.filter(url__exact=url)
        if(len(ret)>0):
            assert(len(ret)==1)
            return ret[0]
        return None

    def update(self, url : (str, list) = None, force : bool = True) -> None:
        assert(isinstance(url, (str, list)) or url is None)
        assert(isinstance(force, bool))

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
        else:
            raise SSD_BadParameterType()


DEFAULT_CONFIG={
    "nodes" : {
        "forward" : [],
        "fallback" : [],
        "other" : []
    }
}

def get_from_default_config(path : str) -> (dict, list, str, int, float, None):
    assert(isinstance(path, str))
    if not path.startswith("config."): return None
    keys = path.split(".")[1:]
    if len(keys)<2: return None

    curr=DEFAULT_CONFIG
    for i in range(len(keys)):
        key = keys[i]
        if key in curr:
            if isinstance(curr, (list, tuple, dict)) and key in curr:
                curr=curr[key]
            else:
                return None
    return curr



class Server:
    _INSTANCE = None

    @staticmethod
    def get_instance():
        if Server._INSTANCE is None:
            Server._INSTANCE = Server()
        return Server._INSTANCE


    def __getitem__(self, item : str) -> (dict, list, str, int, float, None):
        assert(isinstance(item, str))

        val = Value.objects.filter(key__exact=item)
        if len(val)==0:
            default = get_from_default_config(item)
            if default is None:
                return None
            self[item] = default
            return default
        else:
            assert(len(val)==1)
            val=val[0]
            return val.get()

    def __setitem__(self, item : str , value : (dict, list, str, int, float, NoneType)) \
            -> (dict, list, str, int, float, NoneType):
        assert(isinstance(item, str))
        assert(isinstance(value, (dict, list, str, int, float, NoneType)))

        val = Value.objects.filter(key__exact=item)
        if len(val)==0:
            val = Value()
        else:
            val=val[0]
        return val.set(value)

    def __contains__(self, item : str) -> bool:
        val = Value.objects.filter(key__exact=item)
        if len(val) == 0: return False
        return True

    def __init__(self):
        self.nodes=NodeManager()
        self.forward=[]
        self.fallback=[]
        self.url=None

        # chargement de la config
        for section in config.sections():
            for opt in config.options(section):
                key = "config.%s.%s" % (section, opt)
                val = config[section, opt]
                self[key]=val

        allnodes=self["config.nodes.forward"]\
                 +self["config.nodes.fallback"]\
                 +self["config.nodes.other"]


        # chargement de tous les noeuds connus
        self.nodes.update(allnodes)
        # mise à jour des autres noeuds (éventuels)
        self.nodes.update()


        self.forward = [ self.nodes.get(x) for x in self["config.nodes.forward"] ]
        self.fallback = [ self.nodes.get(x) for x in self["config.nodes.fallback"] ]
        self.other = [ self.nodes.get(x) for x in self["config.nodes.other"] ]




    """
        Répond aux url /node/backup/request et /node/forward/request
        L'agent (ou un autre noeud) demande "l'autorisation" avant d'envoyer l'archive de sauvegarde
        Cela permet de savoir si il reste suffisament d'espace disponible et si la
        sauvegarde n'a pas déja été effectué.
        
        En cas de réponse positive un jeton (request_token) est envoyé. Quand le fichier archive
        sera envoyé, le jeton devra être accompagné pour savoir de quelle sauvegarde il s'agit
    """
    def handle_backup_request(self, data : dict , isForward : bool = False) -> SSDError:
        assert isinstance(data, dict)
        assert isinstance(isForward, bool)
        bcr =   ForwardRequest(data, config["infos", "url"]) if isForward else BackupRequest(data)
        log.info("Requête de sauvegarde pour %s.%s taille %s" % (bcr.agent,bcr.backup_name, format_size(bcr.size)))

        du = shutil.disk_usage(config.get_backup_dir())
        left_after = du.total - du.used - bcr.size
        thresold = 0.05 * du.total

        #
        # Calcul de l'espace disponible en prenant une marge (5% du disque doit rester libre après sauvegarde)
        #
        if left_after < thresold:
            missing = thresold - left_after
            log.error("Impossible d'effectuer la sauvegarde de %s.%s, %s d'espace de stockage manquant" %
                      (bcr.agent,bcr.backup_name, format_size(missing)))
            return SSDE_NoFreeSpace(missing)

        #
        # V2rification de la non existence de cette sauvegarde (via backup_hash)
        #
        if Backup.exists(bcr.backup_hash()):
            log.debug("La requête de sauvegarde a déjà été traitée")
            return SSDE_RessourceExists("Le backup '%s' existe déja" % bcr.hash)


        # Enregistrement dans la base de données du backup
        backup = Backup.from_request(bcr) # la fonction fait le save
        log.info("La sauvegarde de %s.%s (%s) est autorisée" %(bcr.agent,bcr.backup_name, format_size(bcr.size)))
        return SSDE_OK({
            "token": backup.request_token
            # permet d'identifier pour la fonction update quelle à quelle sauvegarde le fichier uploadé est lié
        })


    """
        Répond à la /node/backup et /node/forward
        Cette fonction permet de récupérer l'archive de sauvegarde
        soit venant de d'un agent (/node/backup) soit venant d'un
        autre noeud (/node/forward).
        Le fichier dans le corps de POST avec comme nom de fichier 
        'archive'
        
        En cas de réussite (sha3_512 correcte) transmettre la sauvegarde
        aux autres noeuds .
    """
    def handle_backup(self, req : HttpRequest) -> SSDError:
        #vérifications
        log.debug("Envoi de sauvegarde")
        if not "X-upload-token" in req.headers:
            log.error("L'envoi de sauvegarde ne possède pas de token")
            return SSDE_MalformedRequest("L'entête 'X-upload-token' n'est pas passée dans la requête", ["X-upload-token"])
        token = req.headers["X-upload-token"]

        backup = Backup.from_token(token)
        if not backup:
            log.error("Le token demandé (%s) ne correspond à aucune requête de sauvegarde connu" % token)
            raise SSDE_NotFound("La sauvegarde lié au token '%s' n'existe pas" % token, (token,))

        if backup.is_complete:
            log.warning("Le token demandé (%s) a déja été traité" % token)
            raise SSDE_RessourceExists("La sauvegarde lié au token '%s' n'existe pas" % token)

        log.info("Traitement de l'envoi de sauvegarde de %s.%s (%s)" %
                 (backup.agent,backup.backup_name, format_size(backup.size)))


        #écriture du fichier et update du hash
        path = backup.path
        mkdir_rec(join(path, ".."))
        ifd = req.FILES["archive"]
        with open(path, "wb") as ofd:
            hash_sha = hashlib.sha3_512()
            for chunk in ifd.chunks():
                ofd.write(chunk)
                hash_sha.update(chunk)

        #calcul du digest global
        calculated_hash = hash_sha.hexdigest()
        if calculated_hash != backup.hash:
            log.error("Erreur les codes de hachage ne correspondent pas (attendu: '%s', calculé: '%s'"%
                      (backup.hash, calculated_hash))
            return SSDE_CorruptedData("Le code de hachage ne correspond pas", [backup.hash, calculated_hash])

        backup.complete()
        log.info("La sauvegarde a été correctement traité")

        # forward aux autres noeuds via des actions différée
        if backup.forward_left is None: #None -> on transmet self.forward
            for node in self.forward:
                scheduler.forward_backup(config["infos", "url"], backup, node)
        else: # sinon on transmets aux noeuds indiqués dans la requête
            #on vérifie que les noeuds existent bien dans la bas
            scheduler.forward_backup(config["infos", "url"], backup)

        return SSDE_OK()

def init():
    Server.get_instance()