import os
import time

import requests
from django.db import models
from .config import config


INF = float("inf")

def abs_backup(chemin):
    return os.path.abspath(os.path.join(config.get_backup_dir()), chemin)

class Node(models.Model):
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
        SIZE = 64 *1024
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
        for x in range(SIZE): # 64k
            data+="a"

        t1 = time.time()
        res = requests.post(self.url+"/backend/rate")
        if res.status_code == 200:
            self.rate = SIZE /  (time.time() - t1)
        else:
            self.is_connected=False
            self.ping = INF
            self.rate = 0.0
            self.save()
            return
        self.save()




# Create your models here.
class Backup(models.Model):
    creation_date = models.DateTimeField(default=0)
    receive_date = models.DateTimeField(default=0)
    size = models.IntegerField(default=0)
    path = models.TextField()
    hash = models.CharField(max_length=256)
    agent = models.CharField(max_length=256) # ex "Mairie"
    agent_url = models.TextField() # ex "https://mairie.ville-lhermitage:8000/"
    forward_left = models.TextField()


    def move(self, to):
        to = abs_backup(to)
        os.rename(self.chemin, to)
        self.chemin = to
        self.save()

    def remove(self):
        os.remove(self.chemin)
        self.delete()


