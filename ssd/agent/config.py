import json
import configparser
import logging as log

FORMAT = '%(asctime)-15s %(message)s'
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

    def get_entries_name(self):
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
        sections = self.sections()
        #for sec in sections:
        #    sec = Section(self._sections[sec])
        #    self.entries[sec]=BackupEntry(sec, )

    def get_backup_dirs(self, entryname):
        try:
            return self[entryname, "path"]
        except Exception as err:
            log.error("impossible de trouver la liste des dossier à sauvegarder")
            raise Exception()


    def get_temp_dir(self):
        try:
            return self[Config.GLOBAL, "temp"]
        except Exception as err:
            log.error("impossible de trouver le dossier temporaire")
            raise Exception()


    def __getitem__(self, item):
        return json.loads(super().get(item[0], item[1]))



config = Config.instanciate("agent/config_example.cfg")