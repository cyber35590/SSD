import random
import tarfile
import os
import hashlib


from agent.config import log

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

def mkdir_rec(path):
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise Exception("Erreur '%s' n'est pas un dossier....")
    else:
        parent = os.path.abspath(os.path.join(path, ".."))
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise Exception("Erreur '%s' n'est pas un dossier....")
        else:
            mkdir_rec(parent)
        os.mkdir(path)



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

