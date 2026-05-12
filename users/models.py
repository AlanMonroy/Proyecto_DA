from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse

# Create your models here.
def create_user(request):
    username = request.POST['username']
    password = request.POST['password']
    User.objects.create_user(
        username=username,
        password=password
    )

    return HttpResponse("Usuario creado")