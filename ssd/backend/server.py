import shutil

from common.error import SSDE_NoFreeSpace, SSDE_RessourceExists, SSDE_OK, SSDE_NotFound, SSDE_MalformedRequest
from django.core.files.uploadhandler import FileUploadHandler
from .config import config
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

        du = shutil.disk_usage(config.get_backup_dir())
        left_after = du.total - du.used - bcr.size
        thresold = 0.05 * du.total

        if left_after < thresold:
            missing = thresold - left_after
            return SSDE_NoFreeSpace(missing)

        if Backup.exists(bcr.hash):
            return SSDE_RessourceExists("Le backup '%s' existe déja" % bcr.hash)

        backup = Backup.from_request(bcr)
        return SSDE_OK({
            "token": backup.request_token
        })





    def handle_backup(self, token, req):
        backup = Backup.from_token(token)
        if not backup:
            raise SSDE_NotFound("La sauvegarde lié au token '%s' n'existe pas"%token, (token,))

        form = UploadFileForm(req.POST, req.FILES)
        if form.is_valid():
            file = FileUploadHandler()
        else:
            return SSDE_MalformedRequest("Formulaire d'envoi de fichier malfromé")

