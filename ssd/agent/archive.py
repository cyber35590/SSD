import random
import tarfile
import os
import hashlib


from agent.config import log
from common.utils import sha3_512, mkdir_rec
_CHARACTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123789"

def mk_temp_filename(size : int = 16) -> str:
    assert(isinstance(size, int))
    out=""
    for i  in range(size):
        out+=_CHARACTERS[random.randrange(0, len(_CHARACTERS))]
    return out






def make_archive(tmpdir : str, files : list) -> tuple:
    assert(isinstance(files, (list, tuple)))
    for f in files:
        assert(isinstance(f, str) and os.path.exists(f))

    filename = mk_temp_filename()+".tar.xz"
    path = os.path.join(tmpdir, filename)
    log.info("Création de l'archive '%s'"%path)
    mkdir_rec(tmpdir)
    assert os.path.isdir(tmpdir)
    with tarfile.open(path, "w|xz") as tar:
        for file in files:
            log.debug("Ajout du fichier '%s'"%file)
            tar.add(file)
    hash = sha3_512(path)

    assert(isinstance(path, str))
    assert(os.path.isfile(path))
    assert(isinstance(hash, str))
    return path, hash

