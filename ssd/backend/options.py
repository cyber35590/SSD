import json
import os
import time

import requests
from django.db import models
from django.http import HttpRequest


class Value(models.Model):
    key = models.TextField(null=True, blank=True)
    value = models.TextField(null=True, blank=True)

    def get(self):
        return json.loads(self.value)

    def set(self, data):
        self.value = json.dumps(data)



class Options:

    @staticmethod
    def get(key, default=None):
        obj = Value.objects.filter(value__key=key)
        if not obj or len(obj) < 1: return key
        obj = obj[1]
        return obj.get()

    @staticmethod
    def set(key, val):
        obj = Value.objects.filter(value__key=key)
        if not obj or len(obj) < 1:
            obj = Value(key=key, value=val)
        else:
            obj = obj[1]
        obj.set(val)
        obj.save()

    @staticmethod
    def exists(key):
        obj = Value.objects.filter(value__key=key)
        return obj and len(obj) >= 1
