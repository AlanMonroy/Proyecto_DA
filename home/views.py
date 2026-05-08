from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def home(request):
    personas = [
        "Alan",
        "Maria",
        "Juan"
    ]
    return render(request, 'home.html',{
        'personas': personas
    })