import json
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
from django.shortcuts import render

def users(request):
    return render(request, 'users/login.html')

@csrf_exempt
def create_user(request):

    if request.method == 'POST':
        data = json.loads(request.body)
        username = data['username']
        password = data['password']

        User.objects.create_user(
            username=username,
            password=password
        )

        return HttpResponse("Usuario creado")

    return HttpResponse("Metodo no permitido")