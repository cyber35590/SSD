import os
import json
import configparser
import logging as log

FORMAT = '%(asctime)-15s %(message)s'
log.basicConfig(format=FORMAT, level=log.DEBUG)

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
        print(self.sections())
        print(os.getcwd())
        back = self.get_backup_dir()
        if not os.path.exists(back):
            os.mkdir(back, 0o700)
        if not os.path.isdir(back):
            raise Exception("Erreur le chemin spécifié n'est pas un dossier : '%s'" % back)


    def get_backup_dir(self):
        return self[Config.DIRS, "backup"]


    def __getitem__(self, item):
        return json.loads(super().get(item[0], item[1]))



config = Config.instanciate("config_example.cfg")