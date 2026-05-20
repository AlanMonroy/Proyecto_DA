from django.db import models

# Create your models here.

class Refacciones(models.Model):
    refaccion_id = models.BigAutoField(primary_key=True)
    nombre       = models.CharField(max_length=150, unique=True)
    descripcion  = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField()

    class Meta:
        db_table = 'refacciones'
        managed  = False

    def __str__(self):
        return self.nombre  # ← nombre es string, refaccion_id es entero
