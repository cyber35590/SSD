import datetime
import hashlib
import os
import random
import shutil


def disk_usgae_percent(path, n_bytes_to_add=0):
    usage  = shutil.disk_usage(path)
    return 100*(usage.used+n_bytes_to_add)/usage.total

def js_param(js, key, default = None):
    return js[key] if js and key and (key in js) and js[key] is not None else default


INF = float("inf")


_STORAGE_UNIT=[
    [1024, "Kio"],
    [1024*1024, "Mio"],
    [1024*1024*1024, "Gio"],
    [1024*1024*1024*1024, "Tio"],
]

def format_size(n):
    assert isinstance(n, (int, float))
    for i in range(len(_STORAGE_UNIT)):
        if n < _STORAGE_UNIT[i][0] or i==len(_STORAGE_UNIT)-1:
            return "%.2f %s" % (n/_STORAGE_UNIT[i][0], _STORAGE_UNIT[i][1])
    assert False



_ID_CHARS="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-+_"
def new_id(n=32):
    return "".join([random.choice(_ID_CHARS) for _ in range(n)])


def ts2sdate(ts):
    return datetime.datetime.fromtimestamp(ts).strftime()



def sha3_512(filename):
    hash_sha = hashlib.sha3_512()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()

def sha3_512_str(data):
    hash_sha = hashlib.sha3_512()
    hash_sha.update(bytes(data, encoding="utf8"))
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


def join(*pathes):
    return os.path.normpath(os.path.join(*pathes))