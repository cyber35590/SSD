from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404, get_list_or_404
from .config import config




def index(request):
    print()
    return HttpResponse("Hello, world. You're at the polls index.")

"""
    Appelé 
"""
def node_backup_request(request : HttpRequest):
    if request.method == 'POST':

    else:




def node_backup(request):
    pass


def node_forward_request(request):
    pass

def node_forward(request):
    pass
