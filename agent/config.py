import json
import configparser
import logging as log

FORMAT = '%(asctime)-15s %(message)s'
log.basicConfig(format=FORMAT, level=log.DEBUG)
log.warning("Salut")

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

    def get_backup_dirs(self):
        try:
            return self[Config.DIRS, "path"]
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
