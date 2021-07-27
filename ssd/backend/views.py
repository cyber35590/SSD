import json

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from backend.server import Handler
from .config import config
from common.error import *

@csrf_exempt
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")




def response(val):
    if isinstance(val, SSDError):
        if val.ok():
            return JsonResponse(val.to_json())
        return JsonResponse(val.to_json(), status=type(val).HTTP_STATUS)
    else:
        return response(SSDE_OK(val))




"""
    Appelé 
"""

def get_base(req):
    return json.loads(req.body), Handler.get_instance()

@csrf_exempt
def node_ping(request : HttpRequest):
    return response({"length" : len(request.body)})

@csrf_exempt
def node_backup_request(request : HttpRequest):

    if request.method == 'POST':
        data, hand = get_base(request)
        ret = hand.handle_backup_request(data)
        return response(ret)
    else:
        return response(SSDE_MalformedRequest("This url expected only POST requests"))


@csrf_exempt
def node_backup(request : HttpRequest):
    if request.method == 'POST':
        hand = Handler.get_instance()
        ret = hand.handle_backup(request)
        return response(ret)
    else:
        return response(SSDE_MalformedRequest("This url expected only POST requests"))

@csrf_exempt
def node_forward_request(request : HttpRequest):
    pass

@csrf_exempt
def node_forward(request : HttpRequest):
    pass
