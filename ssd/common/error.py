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
        [6, "Unknown error"],
        [7, "No node available"],
        [8, "Corrupted data"],
        [9, "Connection error"]
    ]

    SUCCESS=0
    MALFORMED_JSON=1
    EXISTS=2
    NO_FREE_SPACE=3
    NOT_FOUND=4
    MALFORMED_REQUEST=5
    UNKNOWN_ERROR=6
    NO_NODE_AVAILABLE=7
    CORRUPTED_DATA=8
    CONNECTION_ERROR=9

    def __init__(self, code, msg="Not set", args=None, data=None):
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

    def __getitem__(self, item):
        if isinstance(self.data, dict):
            return self.data[item]
        if isinstance(self.data, (list, tuple)) and isinstance(item, int):
            return self.data[item]
        #todo
        raise Exception()

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
                return SSDError(js["code"], js["message"], js["args"], js["data"])
            except json.decoder.JSONDecodeError as e:
                raise SSDE_MalformedJSON(js, e, "Impossible de charger l'erreur depuis le json")


class SSDE_OK(SSDError):
    HTTP_STATUS=200
    def __init__(self, data=None):
        super().__init__(SSDError.SUCCESS, "Success", data=data)

class SSDE_MalformedJSON(SSDError):
    HTTP_STATUS=400
    def __init__(self, js, err, msg="Impossible de charger le JSON"):
        super().__init__(SSDError.MALFORMED_JSON, msg, [js, err])

class SSDE_RessourceExists(SSDError):
    HTTP_STATUS=409
    def __init__(self, msg):
        super().__init__(SSDError.EXISTS, msg)

class SSDE_NotFound(SSDError):
    HTTP_STATUS=404
    def __init__(self, msg, args=[]):
        super().__init__(SSDError.NOT_FOUND, msg, args)

class SSDE_MalformedRequest(SSDError):
    HTTP_STATUS=400
    def __init__(self, msg, args=[]):
        super().__init__(SSDError.MALFORMED_REQUEST, msg, args)


class SSDE_UnknownError(SSDError):
    HTTP_STATUS=-SSDError.UNKNOWN_ERROR
    def __init__(self, msg="", args=[]):
        super().__init__(SSDError.UNKNOWN_ERROR, msg, args)

class SSDE_NoNodeAvailable(SSDError):
    HTTP_STATUS=-SSDError.NO_NODE_AVAILABLE
    def __init__(self):
        super().__init__(SSDError.UNKNOWN_ERROR, "No node available", [])


class SSDE_CorruptedData(SSDError):
    HTTP_STATUS=406
    def __init__(self, msg, args):
        super().__init__(SSDError.CORRUPTED_DATA, msg, args)


class SSDE_NoFreeSpace(SSDError):
    HTTP_STATUS=507
    def __init__(self, missing_space):
        super().__init__(SSDError.NO_FREE_SPACE, "Espace de stockage insuffisant (%s)" % format_size(missing_space), missing_space)

class SSDE_ConnectionError(SSDError):
    HTTP_STATUS = -SSDError.CONNECTION_ERROR
    def __init__(self, msg, args=[]):
        super().__init__(SSDError.CORRUPTED_DATA, msg, args)
