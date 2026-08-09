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
        return f'{self.proyecto} — {self.empleado}'


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

class Costos(models.Model):
    costo_id = models.BigAutoField(primary_key=True)
    proyecto = models.ForeignKey(
        Proyectos,
        on_delete=models.CASCADE,
        db_column='proyecto_id'
    )
    nombre = models.TextField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)

    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'costos'
        managed = False

    def __str__(self):
        return self.nombre

class Productos(models.Model):
    producto_id = models.BigAutoField(primary_key=True)
    nombre = models.TextField(null=True, blank=True)
    modelo = models.TextField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'productos'
        managed = False

    def __str__(self):
        return self.nombre

class Cotizaciones(models.Model):
    cotizacion_id = models.BigAutoField(primary_key=True)

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        db_column='cliente_id'
    )

    proyecto = models.ForeignKey(
        Proyectos,
        on_delete=models.CASCADE,
        db_column='proyecto_id'
    )
    nombre = models.TextField(null=True, blank=True)
    margen = models.DecimalField(max_digits=10,decimal_places=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    servicio = models.TextField(null=True, blank=True)
    equipo = models.TextField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    pie_cotizacion = models.TextField(null=True, blank=True)

    unidad_cantidad = models.DecimalField(max_digits=10,decimal_places=0)
    unidad_descripcion = models.TextField(null=True, blank=True)
    unidad_costo = models.DecimalField(max_digits=10,decimal_places=2)
    unidad_exportacion = models.DecimalField(max_digits=10,decimal_places=2)
    unidad_margen = models.DecimalField(max_digits=10,decimal_places=0)
    unidad_costo_unitario = models.DecimalField(max_digits=10,decimal_places=2)
    unidad_total = models.DecimalField(max_digits=10,decimal_places=2)


    class Meta:
        db_table = 'cotizaciones'
        managed = False

    def __str__(self):
        return self.nombre

class CotizacionProductos(models.Model):
    cotizacion_producto_id = models.BigAutoField(primary_key=True)
    cotizacion = models.ForeignKey(
        Cotizaciones,
        on_delete=models.CASCADE,
        db_column='cotizacion_id'
    )
    producto = models.ForeignKey(
        Productos,
        on_delete=models.CASCADE,
        db_column='producto_id'
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=0)
    exportacion = models.DecimalField(max_digits=10, decimal_places=2)
    margen = models.DecimalField(max_digits=10, decimal_places=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cotizacion_productos'
        managed = False

    def __str__(self):
        return f'{self.producto} x {self.cantidad}'

class FormatoPdf(models.Model):
    formato_id = models.BigAutoField(primary_key=True)
    empresa_imagen = models.TextField(null=True, blank=True)
    empresa_ubicacion = models.TextField(null=True, blank=True)
    empresa_email = models.TextField(null=True, blank=True)
    empresa_web = models.TextField(null=True, blank=True)
    empresa_telefono = models.TextField(null=True, blank=True)
    contacto_nombre = models.TextField(null=True, blank=True)
    contacto_telefono = models.TextField(null=True, blank=True)
    contacto_ubicacion = models.TextField(null=True, blank=True)
    valido = models.DecimalField(max_digits=10, decimal_places=0)

    class Meta:
        db_table = 'formato_pdf'
        managed = False

    def __str__(self):
        return self.empresa_web

