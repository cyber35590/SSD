import json

from .config import log, config
from .archive import make_archive
import os
import time
import requests
from .entry import Entry
from .node import Node
#time.strftime("%Y_%m_%d-%H_%M_%S")





class Agent:

    def __init__(self):
        self.entries = {}

        for entry in config.get_entries_name():
            self.entries[entry] = Entry.from_config(entry)


    def backup(self, entry=None):

        if entry:
            self.entries[entry].backup()
        else:
            for entry in self.entries:
                self.entries[entry].backup()