from django.urls import path
from . import views

urlpatterns = [
    path('', views.users, name='login'),
    path('create_user', views.create_user),
]