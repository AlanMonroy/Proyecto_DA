from django.db import models

# Create your models here.

class Refacciones(models.Model):
    refaccion_id = models.BigAutoField(primary_key=True)
    nombre       = models.CharField(max_length=150, unique=True)
    descripcion  = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refacciones'
        managed  = False

    def __str__(self):
        return self.nombre  # ← nombre es string, refaccion_id es entero

class Proyectos(models.Model):
    ESTATUS_CHOICES = [
        (1, 'PENDIENTE'),
        (2, 'EN PROCESO'),
        (3, 'FINALIZADO'),
        (4, 'CANCELADO'),
    ]

    PRIORIDAD_CHOICES = [
        (1, 'BAJA'),
        (2, 'MEDIA'),
        (3, 'ALTA'),
        (4, 'CRITICA'),
    ]
    proyecto_id = models.BigAutoField(primary_key=True)
    nombre = models.TextField()
    descripcion = models.TextField(null=True, blank=True)

    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    estatus = models.IntegerField(
        choices=ESTATUS_CHOICES,
        default=0
    )

    prioridad = models.IntegerField(
        choices=PRIORIDAD_CHOICES,
        default=0
    )

    porcentaje_avance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    cotizacion = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    costo_real = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    tipo_proyecto = models.TextField(null=True, blank=True)
    categoria = models.TextField(null=True, blank=True)

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'proyectos'
        managed = False

    def __str__(self):
        return self.nombre
