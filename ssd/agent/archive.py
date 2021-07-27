import random
import tarfile
import os
import hashlib


from agent.config import log
from common.utils import sha3_512, mkdir_rec
_CHARACTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123789"

def mk_temp_filename(size = 16):
    out=""
    for i  in range(size):
        out+=_CHARACTERS[random.randrange(0, len(_CHARACTERS))]
    return out






def make_archive(tmpdir, files):
    filename = mk_temp_filename()+".tar.xz"
    path = os.path.join(tmpdir, filename)
    log.info("Création de l'archive '%s'"%path)
    mkdir_rec(tmpdir)
    assert os.path.isdir(tmpdir)
    with tarfile.open(path, "w|xz") as tar:
        for file in files:
            log.debug("\tAjout du fichier '%s'"%file)
            tar.add(file)
    hash = sha3_512(path)

    return path, hash

