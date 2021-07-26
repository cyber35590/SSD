import json

from .utils import format_size


class SSD_BadFormatException(Exception): pass
class SSD_BadParameterType(Exception): pass
class SSD_ConfigMissingParam(Exception): pass

class SSDError:


    ERRORS=[
        [0, "Success"],
        [1, "Malformed Json"],
        [2, "Ressource exists"],
        [3, "Not enogh free space"],
        [4, "Ressource not found"],
        [5, "Malformed request"],
    ]

    SUCCESS=0
    MALFORMED_JSON=1
    EXISTS=2
    NO_FREE_SPACE=3
    NOT_FOUND=4
    MALFORMED_REQUEST=5

    def __init__(self, code, msg, args=None, data=None):
        if not args: args=[]
        self.code = code
        self.message = msg
        self.args=args # complément de l'erreur
        self.data = data # donne 


    def __bool__(self):
        return self.code==0

    def ok(self):
        return self.code==0

    def err(self):
        return self.code!=0

    def to_json(self):
        return {
            "code" : self.code,
            "data" : self.data,
            "message" : self.message,
            "args" : self.args
        }

    @staticmethod
    def from_json(js):
        if isinstance(js, (str, bytes)):
            try:
                js=json.loads(js)
            except json.decoder.JSONDecodeError as e:
                raise SSDE_MalformedJSON(js, e, "Impossible de charger l'erreur depuis le json")


class SSDE_OK(SSDError):
    def __init__(self, data):
        super().__init__(SSDError.SUCCESS, data=data)

class SSDE_MalformedJSON(SSDError):
    def __init__(self, js, err, msg="Impossible de charger le JSON"):
        super().__init__(SSDError.MALFORMED_JSON, msg, [js, err])

class SSDE_RessourceExists(SSDError):
    def __init__(self, msg):
        super().__init__(SSDError.EXISTS, msg)

class SSDE_NotFound(SSDError):
    def __init__(self, msg, args=[]):
        super().__init__(SSDError.NOT_FOUND, msg, args)

class SSDE_MalformedRequest(SSDError):
    def __init__(self, msg, args=[]):
        super().__init__(SSDError.MALFORMED_REQUEST, msg, args)

        

class SSDE_NoFreeSpace(SSDError):
    def __init__(self, missing_space):
        super().__init__(SSDError.NO_FREE_SPACE, "Espace de stockage insuffisant (%s)" % format_size(missing_space), missing_space)