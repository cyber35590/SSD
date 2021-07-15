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
    return [random.choice(_ID_CHARS) for _ in range(n)]