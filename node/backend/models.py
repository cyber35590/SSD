import json
import os
import time

import requests
from django.db import models
from django.http import HttpRequest

from .config import config


def abs_backup(chemin):
    return os.path.abspath(os.path.join(config.get_backup_dir(), chemin))

from .node import Node
from .server import Server
from .options import Value
