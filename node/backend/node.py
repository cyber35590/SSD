import os
import time

import requests
from django.db import models
from django.http import HttpRequest

from ...common.utils import INF

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

