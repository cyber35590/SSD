import datetime
import json
import os
import time

import requests
from common import utils
from common.backup_request import BackupRequest
from django.db import models
from common.error import *

from .config import config, log

from common.utils import INF, sha3_512_str


def abs_backup(chemin):
    return os.path.abspath(os.path.join(config.get_backup_dir(), chemin))


class Node(models.Model):
    RATE_TEST_SIZE = 128*1024 # Nombre d'octet à envoyer pour tester le débit
    UPDATE_MIN_TIME = 60*60

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
        res = requests.get(self.url+url, *args, **kwargs)
        return SSDError.from_json(res.content)

    def post(self, url, *args, **kwargs):
        res = requests.post(self.url+url, *args, **kwargs)
        return SSDError.from_json(res.content)

    def update(self, force):
        if self.last_update+datetime.timedelta(Node.UPDATE_MIN_TIME)>datetime.datetime.now() or   force:
            self.update_infos()
            self.update_score()
            self.last_update = datetime.datetime.now()
            self.save()

    def update_infos(self):
        ret = self.get("backend/nfos")
        if ret.ok():
            self.site = ret["site"]

        return ret


    #todo mettre toutes les requete avec les méthodes get et post
    def update_score(self):
        t1 = time.time()
        res = requests.get(self.url+"/backend/ping")
        if res.status_code == 200:
            self.ping = (time.time() - t1) * 1000
        else:
            self.is_connected=False
            self.ping = INF
            self.rate = 0.0
            return

        data = ""
        for x in range(Node.RATE_TEST_SIZE): # 64k
            data+="a"

        t1 = time.time()
        res = requests.post(self.url+"/backend/rate")
        if res.status_code == 200:
            self.rate = Node.RATE_TEST_SIZE /  (time.time() - t1)
        else:
            self.is_connected=False
            self.ping = INF
            self.rate = 0.0
            return

    def from_url(self, urls):
        if isinstance(urls, (str)):
            return Node.objects.get(url__exact=urls)
        elif isinstance(urls, (list, tuple)):
            return Node.objects.filter(url__in=urls)
        raise SSD_BadParameterType()


    def transmit_request(self, data):
        pass

    def transmit(self, ):
        pass



def abs_backup(*chemin):
    return os.path.join(config.get_backup_dir(), *chemin)


class Backup(models.Model):
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
    src_node = models.ManyToManyField(Node,blank=True, related_name="backups")

    # Est ce que l'on a récupéré l'archive de sauvegarde
    is_complete = models.BooleanField(default=False)

    # le token de requete
    request_token = models.CharField(max_length=256, null=True, blank = True)

    # hash de lu backup (identifie sur tous les neuds le même backup)
    backup_hash = models.CharField(max_length=256)



    @staticmethod
    def from_request( bc : BackupRequest):
        creation = datetime.datetime.fromtimestamp(bc.creation_date)
        filename = "%s.tar.xz" %(creation.strftime("%Y_%m_%d__%H_%M_%S"))
        path = abs_backup(bc.agent, bc.backup_name, filename)
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
        return ret


    @staticmethod
    def from_token(token):
        res = Backup.objects.filter(request_token__exact=token)

        if len(res): return res[0]
        return None

    def move(self, to):
        to = abs_backup(to)
        os.rename(self.chemin, to)
        self.chemin = to
        self.save()

    def remove(self):
        os.remove(self.chemin)
        self.delete()

    def complete(self):
        self.is_complete=False
        self.save()

    @classmethod
    def exists(cls, hash):
        ret = cls.objects.filter(backup_hash__exact=hash)

        return len(ret) > 0


class Value(models.Model):
    key = models.TextField(null=True, blank=True)
    value = models.TextField(null=True, blank=True)

    def get(self):
        return json.loads(self.value)

    def set(self, data):
        if isinstance(data, str):
            self.value=data
        else:
            self.value = json.dumps(data)
        self.save()
        return data
