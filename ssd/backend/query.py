from backend.models import Node
from common.error import *
from backend.config import config, log

import sys


class Query:

    def __init__(self, type : str, args : dict):
        self.type = type
        self.args = args

    def execute(self):
        return self.run()

    def has_arg(self, key : str , types : (type, None) = None) -> SSDError:
        if key in self.args:
            if (types is None or isinstance(self.args[key], types)):
                return SSDE_OK()
            else:
                return SSDE_MalformedRequest("Le paramètre de la requête '%s' doit être %s (trouvé: %s)"%(
                    key, types, type(self.args[key])
                ))
        return SSDE_MalformedRequest("Le paramètre '%s' est introuvable dans les paramètres" % key)



    def run(self) -> SSDError:
        raise NotImplementedError()

    def get_mandatory_params(self):
        return {}

    def is_valid(self) -> SSDError:
        for k, v in self.get_mandatory_params().items():
            tmp = self.has_arg(k, v)
            if tmp.err():
                return tmp
        return SSDE_OK(self)

    @staticmethod
    def load_from_dict(data : dict) -> SSDError:
        if not isinstance(data, dict):
            return SSDE_MalformedRequest("Les données de la requête doivent être un dict (trouvé: %s)"%type(data).__name__)
        if not "type" in data or not isinstance(data["type"], str):
            log.error("Réception d'une requête invalide ('type' manquant)")
            return SSDE_MalformedRequest("La requête ne possède pas de champs 'type' ou est de mauvais type")

        if not "args" in data or not isinstance(data["args"], str):
            log.error("Réception d'une requête invalide ('args' manquant)")
            return SSDE_MalformedRequest("La requête ne possède pas de champs 'args' ou est de mauvais type")

        t = "Query%s" % data["type"]
        a = data["args"]

        m = sys.modules[__name__]
        if "module" in data:
            if isinstance(data["module"], str):
                try:
                    m = __import__(data["module"])
                except ModuleNotFoundError as err:
                    return SSDE_NotFound("Le module '%s' de la requête '%s' est introuvable, requête impossible..."%(
                        data["module"], t
                    ), (err,))
            else:
                return SSDE_MalformedRequest("Le paramètre optionnel module doit être (quand il est passé) de type str"
                                             "(Trouvé: %s)" % (type(data["module"]).__name__))

        try:
            constr = getattr(m, t)
        except AttributeError as err:
            if "module" in data:
                return SSDE_NotFound("La requête '%s' du module '%s' est introuvable" %(t, data["module"]))
            return SSDE_NotFound("La requête '%s' du module par défaut est introuvable" % t)

        if not isinstance(constr, type) or not issubclass(constr, Query):
            if "module" in data:
                return SSDE_MalformedRequest("Erreur l'éléemnt demandé '%s' du module '%s' n'est pas "
                                             'une requête valide' % (t, data["module"]))
            else:
                return SSDE_MalformedRequest("Erreur l'élément demandé n'est pas une requête valide")

        obj = constr(t, a)
        return obj.is_valid()


    @staticmethod
    def execute_from_dict(data : dict) -> SSDError:
        obj = Query.load_from_dict(data)
        if obj.ok():
            return obj.data.execute()
        return obj


class QueryList(Query):
    def run(self):
        return SSDE_OK(list(map(lambda x: x.as_dict(), Node.objects.all())))
