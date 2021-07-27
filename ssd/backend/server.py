import hashlib
import os
import shutil

from common.error import *
from common.utils import mkdir_rec, join
from django.core.files.uploadhandler import FileUploadHandler
from django.http import HttpRequest

from .config import config, log
from common.backup_request import BackupRequest
from common import utils
from .models import Backup, abs_backup

from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()

class FileUploadHandler(FileUploadHandler):
    """
    Upload handler that streams data into a temporary file.
    """
    def new_file(self, *args, **kwargs):
        """
        Create the file object to append to as data is coming in.
        """
        super().new_file(*args, **kwargs)
        path = abs_backup(utils.new_id())
        du = shutil.disk_usage(config.get_backup_dir())
        if( (du.used+self.content_length) > 0.97*du.total):
            return SSDE_NoFreeSpace(du.used+self.content_length - 0.95*du.total)

        #todo Erreur à traiter
        fd = open(path, "wb")

        self.file = fd

    def receive_data_chunk(self, raw_data, start):
        self.file.write(raw_data)

    def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        return self.file

class Handler:
    _INSTANCE = None

    @staticmethod
    def get_instance():
        if Handler._INSTANCE is None:
            Handler._INSTANCE = Handler()
        return Handler._INSTANCE


    def handle_backup_request(self, data):
        assert isinstance(data, dict)
        bcr = BackupRequest(data)
        log.info("Requête de sauvegarde pour %s.%s taille %s" % (bcr.agent,bcr.backup_name, format_size(bcr.size)))

        du = shutil.disk_usage(config.get_backup_dir())
        left_after = du.total - du.used - bcr.size
        thresold = 0.05 * du.total

        if left_after < thresold:
            missing = thresold - left_after
            log.error("Impossible d'effectuer la sauvegarde de %s.%s, %s d'espace de stockage manquant" %
                      (bcr.agent,bcr.backup_name, format_size(missing)))
            return SSDE_NoFreeSpace(missing)

        if Backup.exists(bcr.backup_hash()):
            log.debug("La requête de sauvegarde a déjà été traitée")
            return SSDE_RessourceExists("Le backup '%s' existe déja" % bcr.hash)

        backup = Backup.from_request(bcr)
        log.info("La sauvegarde de %s.%s (%s) est autorisée" %(bcr.agent,bcr.backup_name, format_size(bcr.size)))
        return SSDE_OK({
            "token": backup.request_token
        })





    def handle_backup(self, req : HttpRequest):
        log.debug("Envoi de sauvegarde")
        if not "X-upload-token" in req.headers:
            log.error("L'envoi de sauvegarde ne possède pas de token")
            return SSDE_MalformedRequest("L'entête 'X-upload-token' n'est pas passée dans la requête", ["X-upload-token"])
        token = req.headers["X-upload-token"]

        backup = Backup.from_token(token)
        if not backup:
            log.error("Le token demandé (%s) ne correspond à aucune requête de sauvegarde connu" % token)
            raise SSDE_NotFound("La sauvegarde lié au token '%s' n'existe pas"%token, (token,))

        log.info("Traitement de l'envoi de sauvegarde de %s.%s (%s)" %
                 (backup.agent,backup.backup_name, format_size(backup.size)))
        
        path = backup.path
        mkdir_rec(join(path, ".."))
        ifd = req.FILES["archive"]
        with open(path, "wb") as ofd:
            hash_sha = hashlib.sha3_512()
            for chunk in ifd.chunks():
                ofd.write(chunk)
                hash_sha.update(chunk)

        calculated_hash = hash_sha.hexdigest()
        if calculated_hash != backup.hash:
            log.error("Erreur les codes de hachage ne correspondent pas (attendu: '%s', calculé: '%s'"%
                      (backup.hash, calculated_hash))
            return SSDE_CorruptedData("Le code de hachage ne correspond pas", [backup.hash, calculated_hash])

        log.info("La sauvegarde a été correctement traité")
        return SSDE_OK()
