import datetime
import json
import os
import time
from django.db.models import Q
import requests
from common import utils
from common.backup_request import BackupRequest, ForwardRequest
from django.db import models
from common.error import *
from django.forms.models import model_to_dict
from .config import config, log

from common.utils import INF, sha3_512_str


def abs_backup(chemin):
    return os.path.abspath(os.path.join(config.get_backup_dir(), chemin))

class Value(models.Model):
    id = models.AutoField(primary_key=True, blank=True, unique=True)
    key = models.TextField(null=True, blank=True)
    value = models.TextField(null=True, blank=True)

    def get(self) -> (dict, list, str, int, float, None):
        return json.loads(self.value)

    def set(self, data) -> (dict, list, str, int, float, None):
        if isinstance(data, str):
            self.value=data
        else:
            self.value = json.dumps(data)
        self.save()
        return data




class Node(models.Model):
    RATE_TEST_SIZE = 512*1024 # Nombre d'octet à envoyer pour tester le débit
    UPDATE_MIN_TIME = 60*60

    id = models.AutoField(primary_key=True, blank=True, unique=True)

    # nom du site
    site = models.CharField(max_length=256, null=True, blank=True)

    # url de base du serveur
    url = models.CharField(max_length=256)

    # ping en ms
    ping = models.FloatField(default=INF)

    # debit en o/s
    rate = models.FloatField(default=0.0)

    # est connecte
    is_connected = models.BooleanField(default=False)

    # date de la dernière mise à jour
    last_update = models.DateTimeField(default=datetime.datetime.fromtimestamp(0))

    def get(self, url, *args, **kwargs):
        assert (isinstance(url, str))
        if len(url) and url[0] == '/':
            url = url[1:]
        url = self.url + url
        return utils.get(url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        assert (isinstance(url, str))
        if len(url) and url[0] == '/':
            url = url[1:]
        url = self.url + url
        return utils.post(url, *args, **kwargs)

    def update(self, force=False):
        if self.last_update.timestamp()+Node.UPDATE_MIN_TIME<datetime.datetime.now().timestamp()\
                or force or not self.is_connected:
            try:
                self.update_infos()
                self.update_score()
                self.last_update = datetime.datetime.now()
                self.save()
            except SSD_BadFormatException as err:
                log.error(str(err))
                pass

    def as_dict(self):
        return {
            "site" : self.site,
            "url" : self.url,
            "is_connected" : self.is_connected,
            "last_update" : self.last_update.timestamp()
        }

    def update_infos(self):
        ret = self.get("/node/infos")
        if ret.ok():
            self.site = ret["site"]

        return ret

    def update_score(self) -> None:
        t1 = time.time()
        url = utils.make_url(self.url, "/node/ping")
        res = utils.get(url)
        if res.ok():
            self.ping = (time.time() - t1) * 1000
        else:
            log.error("Impossible de joindre le serveur '%s' (%s)"%(
                    url, str(res)
            ))
            self.is_connected=False
            self.ping = INF
            self.rate = 0.0
            return

        data = "".join(["a" for _ in range(Node.RATE_TEST_SIZE)])

        t1 = time.time()
        url = utils.make_url(self.url, "/node/ping")
        res = utils.post(url, data=data)
        if res.ok():
            self.rate = Node.RATE_TEST_SIZE /  (time.time() - t1)
        else:
            log.error("Impossible de joindre le serveur '%s' (%s)"%(
                    url, str(res)
            ))
            self.is_connected=False
            self.ping = INF
            self.rate = 0.0
            return
        self.is_connected=True
        log.debug("Noeud '%s' (ping: %3f, rate: %s/s)" % (
            self.site, self.ping, format_size(self.rate)
        ))

    @staticmethod
    def from_present(data : dict):
        url = data["url"]
        if url[-1] != '/': url += "/"
        existing = Node.object.filter(url__exact=url)
        if len(existing) == 0:
            node = Node(url=data["url"], site=data["site"])
        else:
            node = existing[0]
        return node

    @staticmethod
    def from_url(url, create_if_not_exists=False):
        if url[-1]!='/': url+="/"
        if isinstance(url, (str)):
            try:
                return Node.objects.get(url__exact=url)
            except Node.DoesNotExist:
                if create_if_not_exists:
                    x = Node(url=url)
                    x.update()
                    return x
                return None
        raise SSD_BadParameterType()



class Backup(models.Model):
    id = models.AutoField(primary_key=True, blank=True, unique=True)

    # date de création du backup (date de l'agent)
    creation_date = models.DateTimeField(default=0)

    #date de réception du backup (date du server)
    receive_date = models.DateTimeField(default=0)

    # taille en octet du fichier backup
    size = models.IntegerField(default=0)

    # Chemin d'accès local au fichier
    path = models.TextField()

    # hash du fichier
    hash = models.CharField(max_length=256)

    # Nom de l'agent
    agent = models.CharField(max_length=256) # ex "Mairie"

    # Nom de l'entré de sauvegarde
    backup_name = models.CharField(max_length=256) # ex "images" -> Mairie.images

    # Url pour joindre l'agent
    agent_url = models.TextField() # ex "https://mairie.ville-lhermitage:8000/"

    # Liste des noeuds à qui transmettre le backup (et qui ne l'ont pas encore reçus)
    forward_left = models.ManyToManyField(Node, blank=True, related_name="forwarded")

    # Liste des noeuds ou le backup a déja été transmis
    forward_done = models.ManyToManyField(Node,blank=True, related_name="done")

    # Noeud source (uniquement lorsque c'est une transmission d'un autre noeud, =null pour une réception d'un agent)
    src_node = models.ForeignKey(Node,blank=True, related_name="backups", on_delete=models.CASCADE, null=True, default=None)

    # Est ce que l'on a récupéré l'archive de sauvegarde
    is_complete = models.BooleanField(default=False)

    # le token de requete
    request_token = models.CharField(max_length=256, null=True, blank = True)

    # hash de lu backup (identifie sur tous les neuds le même backup)
    # C'est le hash des métadonnées et non de l'archive
    # il est donc unique pour chaque sauvegarde (même si le fichier archive est le même)
    backup_hash = models.CharField(max_length=256)





    @staticmethod
    def from_request( bc : BackupRequest):
        creation = datetime.datetime.fromtimestamp(bc.creation_date)
        filename = "%s.tar.xz" %(creation.strftime("%Y_%m_%d__%H_%M_%S"))
        path = os.path.normpath(
            os.path.join(config["dirs","backup"], bc.agent, bc.backup_name, filename))
        token = utils.new_id()

        ret = Backup(creation_date=datetime.datetime.fromtimestamp(bc.creation_date),
                     receive_date=datetime.datetime.fromtimestamp(time.time()),
                     size=bc.size,
                     path=path,
                     hash=bc.hash,
                     agent=bc.agent,
                     agent_url=bc.agent_url,
                     backup_name=bc.backup_name,
                     request_token=token,
                     backup_hash=bc.backup_hash())

        ret.save()
        #il est nécessaire d'entrer le ligne dans la base avant d'ajouter des clés ManyToMany

        default_forward = config["nodes", "forward"]
        if default_forward is None: default_forward=[]

        #si la requête ne prévoit pas de champ 'forward' (ou forward=None)
        # on prend les forwards par défaut du noeud
        to_forward = default_forward if (bc.forward is None) else bc.forward
        for url in to_forward:
            # si le noeud n'est pas dans la base on le force (create_if_not_exists=True)
            node = Node.from_url(url, create_if_not_exists=True)
            node.update() #update fait le save
            ret.forward_left.add(node)

        # on ajoute le src node si la requête est un forward
        if isinstance(bc, ForwardRequest):
            ret.src_node = Node.from_url(bc.src_node, True)

        ret.save()
        return ret

    def valid_forward(self, node : Node) -> None:
        self.forward_left.remove(node)
        self.forward_done.add(node)
        self.save()




    @staticmethod
    def from_token(token : str):
        res = Backup.objects.filter(request_token__exact=token)

        if len(res): return res[0]
        return None

    def move(self, to) -> None:
        to = abs_backup(to)
        os.rename(self.chemin, to)
        self.chemin = to
        self.save()

    def remove(self) -> None:
        os.remove(self.chemin)
        self.delete()

    def complete(self) -> None:
        self.is_complete=False
        self.save()

    @classmethod
    def exists(cls, hash) -> bool:
        ret = cls.objects.filter(backup_hash__exact=hash)

        return len(ret) > 0

    # permet d'avoir une liste avec les urls des noeuds restants
    def list_forward_left(self, exclude=""):
        return list(map(lambda x: x.url, self.forward_left.filter(~Q(url__exact=exclude))))

    def as_dict(self):
        ret = model_to_dict(self)
        for k, v in ret.items():
            if isinstance(v, datetime.datetime):
                ret[k] = v.timestamp()
        return ret



    def get_source(self):
        if self.src_node:
            return "%s(%s.%s)" % (self.src_node.site, self.agent, self.backup_name)
        else:
            return "%s.%s" % (self.agent, self.backup_name)



class BackupError(models.Model):
    id = models.AutoField(primary_key=True, blank=True, unique=True)
    backup = models.ForeignKey(Backup, related_name="forward_error", on_delete=models.CASCADE)
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    tries = models.IntegerField(default=0, blank=True)
    code = models.IntegerField(default=0, blank=True)
    http_code = models.IntegerField(default=0, blank=True)
    message = models.TextField(blank=True)
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(blank=True)

    @staticmethod
    def set_error(backup : Backup, node: Node, tries : int, err : SSDError):
        be = BackupError(backup=backup, node=node, tries = tries, timestamp=datetime.datetime.now())
        be.code=err.code
        be.http_code = 0
        be.message = str(err)
        be.content = err.to_json()

        backup.forward_left.remove(node)
        be.save()
