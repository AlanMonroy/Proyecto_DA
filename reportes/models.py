from django.db import models

# Create your models here.
class ProyectoEstatus(models.Model):
    estatus_id = models.BigAutoField(primary_key=True)
    nombre = models.TextField()
    color = models.TextField(null=True, blank=True)
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'proyecto_estatus'
        managed = False

    def __str__(self):
        return self.nombre

class ProyectoPrioridad(models.Model):
    prioridad_id = models.BigAutoField(primary_key=True)
    nombre = models.TextField()
    color = models.TextField(null=True, blank=True)
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'proyecto_prioridad'
        managed = False

    def __str__(self):
        return self.nombre

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

class Cliente(models.Model):
    cliente_id = models.BigAutoField(primary_key=True)
    nombre_cliente = models.TextField()
    rfc = models.TextField()
    direccion = models.TextField()
    nombre_contacto = models.TextField()
    email_contacto = models.TextField()
    telefono_contacto = models.TextField()
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cliente'
        managed = False

    def __str__(self):
        return self.nombre_cliente

class Proyectos(models.Model):
    proyecto_id = models.BigAutoField(primary_key=True)
    nombre = models.TextField()
    descripcion = models.TextField(null=True, blank=True)

    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    estatus = models.ForeignKey(
        ProyectoEstatus,
        on_delete=models.PROTECT,
        db_column='estatus'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        db_column='cliente_id'
    )

    prioridad = models.ForeignKey(
        ProyectoPrioridad,
        on_delete=models.PROTECT,
        db_column='prioridad'
    )

    porcentaje_avance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    precio_venta = models.DecimalField(
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

class ProyectoAsignacion(models.Model):
    proyectos_asignacion_id    = models.BigAutoField(primary_key=True)
    proyecto = models.ForeignKey(
        Proyectos,
        on_delete=models.CASCADE,
        db_column='proyecto_id'
    )

    empleado = models.ForeignKey(
        'users.Usuario',
        on_delete=models.CASCADE,
        db_column='empleado_id'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'proyectos_asignacion'
        managed  = False

    def __str__(self):
        return f'{self.proyecto} — {self.usuario}'


class ProyectosActividades(models.Model):
    proyectos_actividades_id = models.BigAutoField(primary_key=True)
    proyecto = models.ForeignKey(
        Proyectos,
        on_delete=models.CASCADE,
        db_column='proyecto_id'
    )

    empleado = models.ForeignKey(
        'users.Usuario',
        on_delete=models.CASCADE,
        db_column='empleado_id'
    )

    actividad_realizada = models.TextField(null=True, blank=True)
    horas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'proyectos_actividades'
        managed = False

    def __str__(self):
        return self.actividad_realizada