from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('backup/request', views.node_backup_request, name='index'),
    path('backup', views.node_backup, name='index'),
    path('forward/request', views.node_forward_request, name='index'),
    path('forward', views.node_forward, name='index'),


]