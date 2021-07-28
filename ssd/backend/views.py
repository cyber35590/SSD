import json

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from backend.server import Server
from .config import config
from common.error import *


def response(val) -> JsonResponse:
    if isinstance(val, SSDError):
        if val.ok():
            return JsonResponse(val.to_json())
        return JsonResponse(val.to_json(), status=type(val).HTTP_STATUS)
    else:
        return response(SSDE_OK(val))





def get_base(req : HttpRequest):
    return json.loads(req.body), Server.get_instance()

@csrf_exempt
def node_ping(request : HttpRequest) -> HttpResponse:
    return response({"length" : len(request.body)})

@csrf_exempt
def node_infos(request : HttpRequest) -> HttpResponse:
    return response({
    })


"""
    Renvoi les urls de tous les noeuds connu localement

"""


@csrf_exempt
def node_list(request: HttpRequest) -> HttpResponse:
    # todo
    pass

"""
    Permet à un autre noeud de se faire connaitre    
"""
@csrf_exempt
def node_discover(request : HttpRequest) -> HttpResponse:
    # todo
    pass



"""
    Permet d'établir des requêts pour acquierir les finformations des autres noeud
    
"""
@csrf_exempt
def node_query(request : HttpRequest) -> HttpResponse:
    # todo
    pass

@csrf_exempt
def node_backup_request(request : HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        data, hand = get_base(request)
        ret = hand.handle_backup_request(data)
        return response(ret)
    else:
        return response(SSDE_MalformedRequest("This url expected only POST requests"))


@csrf_exempt
def node_backup(request : HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        hand = Server.get_instance()
        ret = hand.handle_backup(request)
        return response(ret)
    else:
        return response(SSDE_MalformedRequest("This url expected only POST requests"))


@csrf_exempt
def node_forward_request(request : HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        data, hand = get_base(request)
        ret = hand.handle_backup_request(data, True)
        return response(ret)
    else:
        return response(SSDE_MalformedRequest("This url expected only POST requests"))


@csrf_exempt
def node_forward(request : HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        hand = Server.get_instance()
        ret = hand.handle_request(request)
        return response(ret)
    else:
        return response(SSDE_MalformedRequest("This url expected only POST requests"))



