import datetime
import json
import os
import time

import requests
from common import utils
from common.backup_request import BackupRequest
from django.db import models
from django.http import HttpRequest

from .config import config

from common.utils import INF


def abs_backup(chemin):
    return os.path.abspath(os.path.join(config.get_backup_dir(), chemin))


class Node(models.Model):
    RATE_TEST_SIZE = 128*1024 # Nombre d'octet à envoyer pour tester le débit

    # nom du site
    site = models.CharField(max_length=256)

    # url de base du serveur
    url = models.CharField(max_length=256)

    # ping en ms
    ping = models.FloatField(default=INF)

    # debit en o/s
    rate = models.FloatField(default=0.0)

    # est connecte
    is_connected = models.BooleanField(default=False)

    def update_score(self):
        t1 = time.time()
        res = requests.get(self.url+"/backend/ping")
        if res.status_code == 200:
            self.ping = (time.time() - t1) * 1000
        else:
            self.is_connected=False
            self.ping = INF
            self.rate = 0.0
            self.save()
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
            self.save()
            return
        self.save()

    def transmit_request(self, data):
        pass

    def transmit(self, ):
        pass


def abs_backup(*chemin):
    return os.path.abspath(os.path.join(config.get_backup_dir(), *chemin))


class Backup(models.Model):
    creation_date = models.DateTimeField(default=0)
    receive_date = models.DateTimeField(default=0)
    size = models.IntegerField(default=0)
    path = models.TextField()
    hash = models.CharField(max_length=256)
    agent = models.CharField(max_length=256) # ex "Mairie"
    backup_name = models.CharField(max_length=256) # ex "images" -> Mairie.images
    agent_url = models.TextField() # ex "https://mairie.ville-lhermitage:8000/"
    forward_left = models.ManyToManyField(Node, blank=True)
    forward_done = models.ManyToManyField(Node,blank=True)
    src_node = models.ManyToManyField(Node,blank=True)
    is_complete = models.BooleanField(default=False)
    request_token = models.CharField(max_length=256, null=True, blank = True)

    @staticmethod
    def from_request( bc : BackupRequest):
        creation = datetime.datetime.fromtimestamp(bc.creation_date)
        filename = "%s.tar.xz" %(creation.strftime("%Y_%m_%d__%H_%M_%S"))
        path = abs_backup(bc.agent, bc.backup_name, filename)
        token = utils.new_id()

        ret = Backup(creation_date=bc.creation_date,
                     receive_date=time.time(),
                     size=bc.size,
                     path=path,
                     hash=bc.hash,
                     agent=bc.agent,
                     agent_url=bc.agent_url,
                     backup_name=bc.backup_name,
                     request_token=token)
        ret.save()
        return ret


    @staticmethod
    def from_token(token):
        res = Backup.objects.filter(backup__request_token=token)

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

    @classmethod
    def exists(cls, hash):
        ret = cls.objects.filter(backup__hash=hash)
        return len(ret) > 0

