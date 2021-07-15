import json
import time

from .utils import js_param
from .error import *


class BackupRequest:

    K_CREATION_DATE="create_date"
    K_SIZE="size"
    K_HASH = "hash"
    K_AGENT="agent"
    K_AGENT_URL="agent_url"
    K_BACKUP_NAME="backup_name"
    K_FORWRAD = "forward"

    def __init__(self, data : (str, bytes, dict) = {}):
        if isinstance(data, (str, bytes)):
            try:
                js=json.loads(data)
            except json.decoder.JSONDecodeError as err:
                raise SSDE_MalformedJSON(data, err, "Impossible de charger la requete de sauvegarde, JSON mal formé")
        elif isinstance(data, dict):
            js=data
        else:
            raise Exception("Impoosible de charger la requête, le paramètre du constructeur est invalide", (str, bytes, dict), type(data))

        self.creation_date = js_param(data, BackupRequest.K_CREATION_DATE, time.time())
        self.size = js_param(data, BackupRequest.K_SIZE)
        self.hash = js_param(data, BackupRequest.K_HASH)
        self.agent = js_param(data, BackupRequest.K_AGENT)
        self.agent_url = js_param(data, BackupRequest.K_AGENT_URL)
        self.backup_name = js_param(data, BackupRequest.K_BACKUP_NAME)
        self.forward = js_param(data, BackupRequest.K_FORWRAD)

    def dict(self):
        return {
            BackupRequest.K_CREATION_DATE: self.creation_date ,
            BackupRequest.K_SIZE: self.size,
            BackupRequest.K_HASH: self.hash,
            BackupRequest.K_AGENT: self.agent,
            BackupRequest.K_AGENT_URL: self.agent_url,
            BackupRequest.K_BACKUP_NAME: self.backup_name,
            BackupRequest.K_FORWRAD: self.forward
        }

    def json(self):
        return json.dumps(self.dict())


