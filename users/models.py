from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Usuario(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    email    = models.EmailField(unique=True)
    rol_id   = models.IntegerField(default=1)

    class Meta:
        db_table = 'usuarios'  # ← apunta a tu tabla existente en Supabase
        managed  = False       # ← Django no toca la tabla (no crea ni borra nada)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username

class MenuOpcion(models.Model):
    opcion_id = models.BigAutoField(primary_key=True)
    nombre    = models.CharField(max_length=100)
    url_name  = models.CharField(max_length=100)
    rol_id    = models.IntegerField()
    orden     = models.IntegerField(default=0)

    class Meta:
        db_table = 'menu_opciones'
        managed  = False
        ordering = ['orden']
