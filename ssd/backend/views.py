import json

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from backend.server import Handler
from .config import config

@csrf_exempt
def index(request):
    print()
    return HttpResponse("Hello, world. You're at the polls index.")

"""
    Appelé 
"""
@csrf_exempt
def node_backup_request(request : HttpRequest):
    if request.method == 'POST':
        data = json.loads(request.body)
        hand = Handler.get_instance()
        hand.handle_backup_request(data)
    else:
        pass


@csrf_exempt
def node_backup(request : HttpRequest):
    pass

@csrf_exempt
def node_forward_request(request : HttpRequest):
    pass

@csrf_exempt
def node_forward(request : HttpRequest):
    pass
