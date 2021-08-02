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
    return json.loads(str(req.body, encoding="utf8")), Server.get_instance()

@csrf_exempt
def node_ping(request : HttpRequest) -> HttpResponse:
    return response({"length" : len(request.body)})

@csrf_exempt
def node_infos(request : HttpRequest) -> HttpResponse:
    return response({
        "site" : config["infos", "site"],
        "forward" : config["nodes", "forward"],
        "other" : config["nodes", "other"],
        "fallback" : config["nodes", "fallback"],
        "url" : config["infos", "url"]
    })



"""
    Permet à un autre noeud de se faire connaitre    
"""
@csrf_exempt
def node_present(request : HttpRequest) -> HttpResponse:
    # todo vérification de sécurité....
    if request.method == "POST":
        js, serv = get_base(request)
        return response(serv.handle_node_present(js))

    else:
        return response(SSDE_NotFound("L'url /node/present ne peut être utilisée qu'avec POST"))



"""
    Permet d'établir des requêts pour acquierir les finformations des autres noeud
    
"""
@csrf_exempt
def node_query(request : HttpRequest) -> HttpResponse:
    # todo
    if request.method == "POST":
        js, serv = get_base(request)
        return response(serv.handle_node_query(js))
    else:
        return response(SSDE_NotFound("L'url /node/query ne peut être utilisée qu'avec POST"))


@csrf_exempt
def node_backup_request(request : HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        data, hand = get_base(request)
        ret = hand.handle_backup_request(data, False)
        return response(ret)
    else:
        return response(SSDE_MalformedRequest("This url expected only POST requests"))


@csrf_exempt
def node_backup(request : HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        hand = Server.get_instance()
        ret = hand.handle_backup(request, False)
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
        ret = hand.handle_backup(request, True)
        return response(ret)
    else:
        return response(SSDE_MalformedRequest("This url expected only POST requests"))



