import json
import configparser
import logging as log
from ..common.error import *

FORMAT = '%(asctime)-15s %(message)s'
log.basicConfig(format=FORMAT, level=log.DEBUG)

class Option:
    def __init__(self, k, v):
        self.name = k
        self.value=v

class Section(dict):
    def __init__(self, name, content):
        super().__init__()
        self.name = name
        for k in content:
            self[k]=Option(k, content[k])





class Parameter:

    def __init__(self, name, mandatory=True, default=None):
        self.name=name
        self.mandatory=mandatory
        self.default=default

    def get_value(self, section, section_default):
        if self.name in section: return section[self.name]
        if self.name in section_default: return section_default[self.name]
        if self.mandatory:
            raise SSD_ConfigMissingParam("Valeur manquante dans la configuration: %s.%s "%(self.sectionname, self.name))
        return self.default


class BackupEntry:
    DEFAULT=[
             Parameter("path"),
             Parameter("default_url"),
             Parameter("fallback_urls")
    ]

    def __init__(self, section, default):
        self.section_name
        for opt in BackupEntry.DEFAULT:
            setattr(self, opt.name, opt.get_value(section, default))




class Config(configparser.ConfigParser):
    DIRS="dirs"
    _INSTANCE=None

    @staticmethod
    def instanciate(files, default=None):
        Config._INSTANCE=Config(files, default)
        return Config._INSTANCE

    def get_instance(self):
        return self._INSTANCE

    def __init__(self, files, default):
        super().__init__()
        if isinstance(files, str): files=[files]
        self.files=files
        self.read(self.files)
        self.entries={}
        sections = self.sections()
        for sec in sections:
            sec = Section(self._sections[sec])
            self.entries[sec]=BackupEntry(sec, )



    def get_backup_dirs(self, entryname):
        try:
            return self[entryname, "path"]
        except Exception as err:
            log.error("impossible de trouver la liste des dossier à sauvegarder")
            raise Exception()

    def get_temp_dir(self):
        try:
            return self[Config.DIRS, "temp"]
        except Exception as err:
            log.error("impossible de trouver le dossier temporaire")
            raise Exception()


    def __getitem__(self, item):
        return json.loads(super().get(item[0], item[1]))



config = Config.instanciate("agent/config_example.cfg")