import random
import tarfile
import os
import hashlib


from common.config_base import log

_CHARACTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123789"

def mk_temp_filename(size = 16):
    out=""
    for i  in range(size):
        out+=_CHARACTERS[random.randrange(0, len(_CHARACTERS))]
    return out


def sha3_512(filename):
    hash_sha = hashlib.sha3_512()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


def make_archive(tmpdir, files):
    filename = mk_temp_filename()+".tar.xz"
    path = os.path.join(tmpdir, filename)
    log.info("Création de l'archive '%s'"%path)
    with tarfile.open(path, "w|xz") as tar:
        for file in files:
            log.debug("\tAjout du fichier '%s'"%file)
            tar.add(file)
    hash = sha3_512(path)
    return path, hash

