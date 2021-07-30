import datetime
import hashlib
import os
import random
import shutil
import requests
from common.error import *

def disk_usgae_percent(path, n_bytes_to_add=0):
    usage  = shutil.disk_usage(path)
    return 100*(usage.used+n_bytes_to_add)/usage.total

def js_param(js, key, default = None):
    return js[key] if js and key and (key in js) and js[key] is not None else default

def join(*args):
    return os.path.normpath(os.path.join(*args))


_ID_CHARS="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-+_"
def new_id(n : int = 32) -> str:
    return "".join([random.choice(_ID_CHARS) for _ in range(n)])


def sha3_512(filename : str) -> str:
    assert isinstance(filename, str)
    assert os.path.isfile(filename)

    hash_sha = hashlib.sha3_512()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()

def sha3_512_str(data : (str, bytes)) -> str:
    hash_sha = hashlib.sha3_512()
    hash_sha.update(bytes(data, encoding="utf8"))
    return hash_sha.hexdigest()

def mkdir_rec(path : str) -> None:
    assert isinstance(path, str)
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


def get(url, *args, **kwargs) -> SSDError:
    assert(isinstance(url, str))
    if len(url) and url[0]=='/':
        url=url[1:]
    try:
        res = requests.get(url, *args, **kwargs)
    except requests.exceptions.ConnectionError as err:
        if isinstance(err.args[0], (Exception)):
            err = err.args[0]
            if hasattr(err, "reason"):
                return SSDE_ConnectionError("Impossible de joindre le serveur (%s) : %s" %(url, err.reason), (url,))
        return SSDE_ConnectionError(str(err))
    return SSDError.from_json(res.content)

def post(url, *args, **kwargs) -> SSDError:
    assert(isinstance(url, str))
    if len(url) and url[0]=='/':
        url=url[1:]
    try:
        res = requests.post(url, *args, **kwargs)
    except requests.exceptions.ConnectionError as err:
        if isinstance(err.args[0], (Exception)):
            err = err.args[0]
        return SSDE_ConnectionError("Impossible de joindre le serveur (%s) : %s" %
                                    (url, err.reason if hasattr(err, "reason") else str(err)), (url,))
    return SSDError.from_json(res.content)

def make_url(*args):
    out=""
    for path in args:
        path=str(path)
        if path[0] == "/": path = path[1:]
        if path[-1] != "/" : path+="/"
        out+=path
    return out if out[-1]!="/" else out[:-1]

NoneType=type(None)