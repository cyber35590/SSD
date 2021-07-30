import json
import configparser
import logging as log
import os


FORMAT = '%(asctime)-15s|%(levelname)-8s %(message)s'
log.basicConfig(format=FORMAT, level=log.DEBUG)




class Config(configparser.ConfigParser):
    GLOBAL="global"
    _INSTANCE=None

    @staticmethod
    def instanciate(files, default=None):
        Config._INSTANCE=Config(files, default)
        return Config._INSTANCE

    def get_instance(self):
        return self._INSTANCE

    @staticmethod
    def get_entries_name():
        EXCLUDE = ["global"]
        out = []
        for n in config.sections():
            if not n in EXCLUDE: out.append(n)

        return out

    def __init__(self, files, default):
        super().__init__()
        if isinstance(files, str): files=[files]
        self.files=files
        self.read(self.files)
        self.entries={}
        #for sec in sections:
        #    sec = Section(self._sections[sec])
        #    self.entries[sec]=BackupEntry(sec, )

    def get_backup_dirs(self, entryname):
        try:
            return self[entryname, "path"]
        except KeyError:
            log.critical("impossible de trouver la liste des dossier à sauvegarder")
            assert(False)


    def get_temp_dir(self):
        try:
            return self[Config.GLOBAL, "temp"]
        except KeyError:
            log.critical("impossible de trouver le dossier temporaire")
            assert(False)


    def __getitem__(self, item):
        try:
            return json.loads(super().get(item[0], item[1]))
        except configparser.NoOptionError as err:
            return None

config_files = ["agent/config.cfg", "agent/config_example.cfg"]
if "AGENT_CONFIG" in os.environ:
    config_files = os.environ.get("AGENT_CONFIG")
config = Config.instanciate(config_files)