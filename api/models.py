from django.db import models, transaction
from django.db.models import Sum
# Create your models here.

from django.utils import timezone
from datetime import date
from decimal import Decimal


from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


def validar_anio_vehiculo(value: int) -> None:
    """
    Evita registrar años demasiado antiguos o muy superiores
    al año actual.
    """
    anio_actual = date.today().year

    if value < 1950:
        raise ValidationError(
            "El año del vehículo no puede ser menor a 1950."
        )

    if value > anio_actual + 1:
        raise ValidationError(
            f"El año del vehículo no puede ser mayor a {anio_actual + 1}."
        )


class Usuario(AbstractUser):
    """
    Usuario personalizado para autenticación y control de acceso.
    """

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        EMPLEADO = "EMPLEADO", "Empleado"
        CLIENTE = "CLIENTE", "Cliente"

    email = models.EmailField(
        unique=True,
        verbose_name="correo electrónico",
    )
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
    )

    def save(self, *args, **kwargs):
        # Un superusuario siempre debe tener permisos administrativos.
        if self.is_superuser:
            self.rol = self.Rol.ADMIN
            self.is_staff = True

        super().save(*args, **kwargs)

    def __str__(self):
        nombre_completo = self.get_full_name().strip()

        if nombre_completo:
            return f"{nombre_completo} ({self.username})"

        return self.username


class Cliente(models.Model):
    """
    Información del cliente del taller.

    Un cliente puede estar relacionado con una cuenta de usuario
    o existir únicamente como cliente presencial sin acceso al sistema.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="cliente",
        null=True,
        blank=True,

    )
    nombres = models.CharField(
        max_length=100,
    )

    apellidos = models.CharField(
        max_length=100,
        blank=True,
    )

    identificacion = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
    )
    email = models.EmailField(
        blank=True,
    )
    direccion = models.CharField(
        max_length=255,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "nombres",
            "apellidos",
            "id",
        ]

    def clean(self):
        if self.usuario_id and self.usuario.rol != Usuario.Rol.CLIENTE:
            raise ValidationError(
                {
                    "usuario": (
                        "El usuario relacionado debe tener el rol CLIENTE."
                    )
                }
            )

    def __str__(self):
        nombre_completo = (
            f"{self.nombres} {self.apellidos}"
        ).strip()

        if nombre_completo:
            return nombre_completo

        if self.identificacion:
            return self.identificacion

        return f"Cliente {self.pk}"


class Marca(models.Model):
    nombre = models.CharField(
        max_length=80,
        unique=True,
    )
    pais_origen = models.CharField(
        max_length=80,
        blank=True,
    )
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().title()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class ModeloVehiculo(models.Model):
    class TipoVehiculo(models.TextChoices):
        AUTOMOVIL = "AUTOMOVIL", "Automóvil"
        SUV = "SUV", "SUV"
        CAMIONETA = "CAMIONETA", "Camioneta"
        CAMION = "CAMION", "Camión"
        MOTOCICLETA = "MOTOCICLETA", "Motocicleta"
        FURGONETA = "FURGONETA", "Furgoneta"
        OTRO = "OTRO", "Otro"

    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name="modelos",
    )
    nombre = models.CharField(max_length=100)
    tipo_vehiculo = models.CharField(
        max_length=20,
        choices=TipoVehiculo.choices,
        default=TipoVehiculo.AUTOMOVIL,
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["marca__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["marca", "nombre"],
                name="modelo_unico_por_marca",
            )
        ]

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().title()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.marca.nombre} {self.nombre}"


class Vehiculo(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="vehiculos",
    )
    modelo_vehiculo = models.ForeignKey(
        ModeloVehiculo,
        on_delete=models.PROTECT,
        related_name="vehiculos",
    )
    placa = models.CharField(
        max_length=15,
        unique=True,
    )
    anio = models.PositiveIntegerField(
        validators=[validar_anio_vehiculo],
    )
    color = models.CharField(
        max_length=50,
        blank=True,
    )
    kilometraje_actual = models.PositiveIntegerField(
        default=0,
    )
    numero_chasis = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["placa"]

    def save(self, *args, **kwargs):
        self.placa = self.placa.strip().upper()

        if self.numero_chasis:
            self.numero_chasis = self.numero_chasis.strip().upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.placa} - "
            f"{self.modelo_vehiculo.marca.nombre} "
            f"{self.modelo_vehiculo.nombre}"
        )


class Servicio(models.Model):
    nombre = models.CharField(
        max_length=120,
        unique=True,
    )
    descripcion = models.TextField(
        blank=True,
    )
    precio_referencial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    foto = models.ImageField(
        upload_to="servicios/",
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    visible_publicamente = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
    
    ##ESPECIALIDAD
class Especialidad(models.Model):
    """
    Catálogo de especialidades que puede tener un empleado.
    """

    nombre = models.CharField(
        max_length=80,
        unique=True,
    )

    descripcion = models.TextField(
        blank=True,
    )

    activa = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Especialidad"
        verbose_name_plural = "Especialidades"

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().title()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
    
    ##EMPLEADO DEL TALLER

class Empleado(models.Model):
    """
    Información laboral del personal del taller.

    El acceso al sistema lo controla Usuario.
    Este modelo almacena únicamente información
    relacionada con el trabajo dentro del taller.
    """

    class Cargo(models.TextChoices):
        ADMINISTRADOR = (
            "ADMINISTRADOR",
            "Administrador",
        )

        RECEPCIONISTA = (
            "RECEPCIONISTA",
            "Recepcionista",
        )

        MECANICO = (
            "MECANICO",
            "Mecánico",
        )

        SUPERVISOR = (
            "SUPERVISOR",
            "Supervisor",
        )

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="empleado",
    )

    cargo = models.CharField(
        max_length=20,
        choices=Cargo.choices,
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
    )

    fecha_ingreso = models.DateField()

    especialidades = models.ManyToManyField(
        Especialidad,
        blank=True,
        related_name="empleados",
    )

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "usuario__first_name",
            "usuario__last_name",
        ]
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def clean(self):
        if self.usuario.rol != Usuario.Rol.EMPLEADO:
            raise ValidationError(
                {
                    "usuario": (
                        "El usuario debe tener el rol EMPLEADO."
                    )
                }
            )

    @property
    def nombre_completo(self):
        return (
            self.usuario.get_full_name()
            or self.usuario.username
        )

    def __str__(self):
        return (
            f"{self.nombre_completo}"
            f" - "
            f"{self.get_cargo_display()}"
        )
    

    ##CONSECUTIVO ORDEN MODELO QUE NO SE MOSTRARA SOLO SIRVE PARA ORDENAR LA SECUENCIA DE ORDENES DE TRABAJO # DE ORDEN 
class ConsecutivoOrden(models.Model):
    """
    Guarda el último número de orden utilizado durante cada año.

    Ejemplo:
    año 2026 -> último número 15
    próxima orden -> OT-2026-000016
    """

    anio = models.PositiveIntegerField(
        unique=True,
    )
    ultimo_numero = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["-anio"]
        verbose_name = "Consecutivo de orden"
        verbose_name_plural = "Consecutivos de órdenes"

    def __str__(self):
        return f"{self.anio}: {self.ultimo_numero}"

    #ORDEN DE TRBAJO

    ##FLUJO DE CLIENTE 
class Cita(models.Model):
    class Estado(models.TextChoices):
        SOLICITADA = "SOLICITADA", "Solicitada"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        REPROGRAMADA = "REPROGRAMADA", "Reprogramada"
        CANCELADA = "CANCELADA", "Cancelada"
        ATENDIDA = "ATENDIDA", "Atendida"
        NO_ASISTIO = "NO_ASISTIO", "No asistió"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="citas",
    )
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name="citas",
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.SET_NULL,
        related_name="citas",
        null=True,
        blank=True,
    )
    fecha_solicitada = models.DateTimeField()
    motivo = models.CharField(
        max_length=255,
    )
    observaciones_cliente = models.TextField(
        blank=True,
    )
    respuesta_taller = models.TextField(
        blank=True,
    )
    motivo_cancelacion = models.TextField(
        blank=True,
    )
    
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.SOLICITADA,
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-fecha_solicitada"]

    def clean(self):
        if (
            self.vehiculo_id
            and self.cliente_id
            and self.vehiculo.cliente_id != self.cliente_id
        ):
            raise ValidationError(
                {
                    "vehiculo": (
                        "El vehículo seleccionado no pertenece al cliente."
                    )
                }
            )

    def __str__(self):
        return (
            f"Cita #{self.pk or 'nueva'} - "
            f"{self.vehiculo.placa} - "
            f"{self.get_estado_display()}"
        )
    
class OrdenTrabajo(models.Model):
    class Estado(models.TextChoices):
        RECIBIDO = "RECIBIDO", "Recibido"
        EN_REVISION = "EN_REVISION", "En revisión"
        ESPERANDO_AUTORIZACION = (
            "ESPERANDO_AUTORIZACION",
            "Esperando autorización",
        )
        EN_REPARACION = "EN_REPARACION", "En reparación"
        EN_LAVADO = "EN_LAVADO", "En lavado"
        LISTO = "LISTO", "Listo para retirar"
        ENTREGADO = "ENTREGADO", "Entregado"
        CANCELADO = "CANCELADO", "Cancelado"

    numero_orden = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
    )

    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name="ordenes",
    )

    cita = models.OneToOneField(
        Cita,
        on_delete=models.SET_NULL,
        related_name="orden_trabajo",
        null=True,
        blank=True,
    )

    empleado_recepciona = models.ForeignKey(
        Empleado,
        on_delete=models.PROTECT,
        related_name="ordenes_recibidas",
    )

    empleado_responsable = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        related_name="ordenes_asignadas",
        null=True,
        blank=True,
    )

    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.RECIBIDO,
    )

    motivo_ingreso = models.CharField(
        max_length=250,
    )

    observaciones_recepcion = models.TextField(
        blank=True,
    )

    kilometraje_ingreso = models.PositiveIntegerField()

    fecha_ingreso = models.DateTimeField(
        default=timezone.now,
    )

    fecha_estimada_entrega = models.DateField(
        null=True,
        blank=True,
    )

    fecha_entrega = models.DateTimeField(
        null=True,
        blank=True,
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-fecha_ingreso"]
        verbose_name = "Orden de trabajo"
        verbose_name_plural = "Órdenes de trabajo"

    def clean(self):
        errores = {}

        if (
            self.cita_id
            and self.vehiculo_id
            and self.cita.vehiculo_id != self.vehiculo_id
        ):
            errores["cita"] = (
                "La cita seleccionada no pertenece al vehículo "
                "de esta orden."
            )

        if (
            self.empleado_responsable_id
            and self.empleado_responsable.cargo
            != Empleado.Cargo.MECANICO
        ):
            errores["empleado_responsable"] = (
                "El empleado responsable debe tener el cargo de mecánico."
            )

        if (
            self.fecha_estimada_entrega
            and self.fecha_ingreso
            and self.fecha_estimada_entrega
            < self.fecha_ingreso.date()
        ):
            errores["fecha_estimada_entrega"] = (
                "La fecha estimada de entrega no puede ser anterior "
                "a la fecha de ingreso."
            )

        if (
            self.fecha_entrega
            and self.fecha_ingreso
            and self.fecha_entrega < self.fecha_ingreso
        ):
            errores["fecha_entrega"] = (
                "La fecha de entrega no puede ser anterior "
                "a la fecha de ingreso."
            )

        if self.descuento > self.subtotal:
            errores["descuento"] = (
                "El descuento no puede superar el subtotal."
            )

        if self.estado == self.Estado.ENTREGADO and not self.fecha_entrega:
            errores["fecha_entrega"] = (
                "Una orden entregada debe tener una fecha de entrega."
            )

        if (
            self.fecha_entrega
            and self.estado != self.Estado.ENTREGADO
        ):
            errores["estado"] = (
                "Si existe una fecha de entrega, el estado debe ser "
                "ENTREGADO."
            )

        if errores:
            raise ValidationError(errores)

    def generar_numero_orden(self):
        """
        Genera un número de orden consecutivo por año.

        Ejemplos:
        OT-2026-000001
        OT-2026-000002
        """
        anio = self.fecha_ingreso.year

        consecutivo, _ = (
            ConsecutivoOrden.objects
            .select_for_update()
            .get_or_create(
                anio=anio,
                defaults={
                    "ultimo_numero": 0,
                },
            )
        )

        consecutivo.ultimo_numero += 1
        consecutivo.save(
            update_fields=["ultimo_numero"],
        )

        return (
            f"OT-"
            f"{anio}-"
            f"{consecutivo.ultimo_numero:06d}"
        )

    def calcular_total(self):
        total_calculado = self.subtotal - self.descuento
        return max(total_calculado, Decimal("0.00"))

    def recalcular_totales(self):
        """
        Recalcula el subtotal y total utilizando los servicios
        que no estén rechazados ni cancelados.
        """
        resultado = self.detalles_servicios.exclude(
            estado__in=[
                DetalleServicioOrden.Estado.RECHAZADO,
                DetalleServicioOrden.Estado.CANCELADO,
            ]
        ).aggregate(
            subtotal_calculado=Sum("subtotal")
        )

        subtotal = (
            resultado["subtotal_calculado"]
            or Decimal("0.00")
        )

        descuento = min(
            self.descuento,
            subtotal,
        )

        total = subtotal - descuento

        OrdenTrabajo.objects.filter(
            pk=self.pk,
        ).update(
            subtotal=subtotal,
            descuento=descuento,
            total=total,
        )

        self.subtotal = subtotal
        self.descuento = descuento
        self.total = total
        
    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.numero_orden:
                self.numero_orden = self.generar_numero_orden()

            self.total = self.calcular_total()

            super().save(*args, **kwargs)

    def __str__(self):
        return self.numero_orden or "Orden de trabajo sin número"

class HistorialEstadoOrden(models.Model):
    """
    Registra la línea de tiempo de estados de una orden de trabajo.

    Los registros representan eventos históricos y no deberían
    modificarse después de su creación.
    """

    orden = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="historial_estados",
    )

    estado_anterior = models.CharField(
        max_length=30,
        choices=OrdenTrabajo.Estado.choices,
        null=True,
        blank=True,
    )

    estado_nuevo = models.CharField(
        max_length=30,
        choices=OrdenTrabajo.Estado.choices,
    )

    titulo = models.CharField(
        max_length=150,
    )

    descripcion = models.TextField(
        blank=True,
    )

    visible_cliente = models.BooleanField(
        default=True,
    )

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        related_name="cambios_estado_realizados",
        null=True,
        blank=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["creado_en"]
        verbose_name = "Historial de estado de orden"
        verbose_name_plural = "Historiales de estados de órdenes"
        indexes = [
            models.Index(
                fields=["orden", "creado_en"],
                name="historial_orden_fecha_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.orden.numero_orden} - "
            f"{self.get_estado_nuevo_display()}"
        )
    


class Diagnostico(models.Model):
    class Gravedad(models.TextChoices):
        INFORMATIVO = "INFORMATIVO", "Informativo"
        LEVE = "LEVE", "Leve"
        MODERADO = "MODERADO", "Moderado"
        URGENTE = "URGENTE", "Urgente"

    class EstadoRespuesta(models.TextChoices):
        NO_REQUERIDA = "NO_REQUERIDA", "No requerida"
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"

    orden = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="diagnosticos",
    )

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.PROTECT,
        related_name="diagnosticos_realizados",
    )

    titulo = models.CharField(
        max_length=150,
    )

    descripcion = models.TextField()

    gravedad = models.CharField(
        max_length=20,
        choices=Gravedad.choices,
        default=Gravedad.INFORMATIVO,
    )

    requiere_autorizacion = models.BooleanField(
        default=False,
    )

    estado_respuesta = models.CharField(
        max_length=20,
        choices=EstadoRespuesta.choices,
        default=EstadoRespuesta.NO_REQUERIDA,
    )

    comentario_cliente = models.TextField(
        blank=True,
    )

    fecha_respuesta = models.DateTimeField(
        null=True,
        blank=True,
    )

    visible_cliente = models.BooleanField(
        default=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"
        indexes = [
            models.Index(
                fields=["orden", "estado_respuesta"],
                name="diag_orden_respuesta_idx",
            ),
        ]

    def clean(self):
        errores = {}

        if self.empleado_id:
            if not self.empleado.activo:
                errores["empleado"] = (
                    "El empleado que registra el diagnóstico debe estar activo."
                )

            if self.empleado.cargo != Empleado.Cargo.MECANICO:
                errores["empleado"] = (
                    "El diagnóstico debe ser registrado por un mecánico."
                )

        if self.requiere_autorizacion:
            if self.estado_respuesta == self.EstadoRespuesta.NO_REQUERIDA:
                self.estado_respuesta = self.EstadoRespuesta.PENDIENTE
        else:
            if self.estado_respuesta in {
                self.EstadoRespuesta.PENDIENTE,
                self.EstadoRespuesta.APROBADO,
                self.EstadoRespuesta.RECHAZADO,
            }:
                errores["estado_respuesta"] = (
                    "Un diagnóstico que no requiere autorización "
                    "debe usar el estado NO_REQUERIDA."
                )

        if (
            self.estado_respuesta
            in {
                self.EstadoRespuesta.APROBADO,
                self.EstadoRespuesta.RECHAZADO,
            }
            and not self.fecha_respuesta
        ):
            errores["fecha_respuesta"] = (
                "Una respuesta aprobada o rechazada debe registrar su fecha."
            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        if self.requiere_autorizacion:
            if not self.estado_respuesta:
                self.estado_respuesta = self.EstadoRespuesta.PENDIENTE

            if self.estado_respuesta == self.EstadoRespuesta.NO_REQUERIDA:
                self.estado_respuesta = self.EstadoRespuesta.PENDIENTE
        else:
            self.estado_respuesta = self.EstadoRespuesta.NO_REQUERIDA
            self.comentario_cliente = ""
            self.fecha_respuesta = None

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.orden.numero_orden} - "
            f"{self.titulo}"
        )
    


class DetalleServicioOrden(models.Model):
    class Estado(models.TextChoices):
        PROPUESTO = "PROPUESTO", "Propuesto"
        AUTORIZADO = "AUTORIZADO", "Autorizado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        COMPLETADO = "COMPLETADO", "Completado"
        CANCELADO = "CANCELADO", "Cancelado"

    orden = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="detalles_servicios",
    )

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name="detalles_orden",
    )

    diagnostico = models.ForeignKey(
        Diagnostico,
        on_delete=models.SET_NULL,
        related_name="servicios_propuestos",
        null=True,
        blank=True,
    )

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        related_name="servicios_realizados",
        null=True,
        blank=True,
    )

    descripcion = models.TextField(
        blank=True,
    )

    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROPUESTO,
    )

    visible_cliente = models.BooleanField(
        default=True,
    )

    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_finalizacion = models.DateTimeField(
        null=True,
        blank=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["creado_en"]
        verbose_name = "Detalle de servicio de orden"
        verbose_name_plural = "Detalles de servicios de órdenes"
        indexes = [
            models.Index(
                fields=["orden", "estado"],
                name="detalle_orden_estado_idx",
            ),
        ]

    def clean(self):
        errores = {}

        if self.orden_id and self.orden.estado in {
            OrdenTrabajo.Estado.ENTREGADO,
            OrdenTrabajo.Estado.CANCELADO,
        }:
            errores["orden"] = (
                "No se pueden agregar o modificar servicios en una "
                "orden entregada o cancelada."
            )

        if (
            self.diagnostico_id
            and self.orden_id
            and self.diagnostico.orden_id != self.orden_id
        ):
            errores["diagnostico"] = (
                "El diagnóstico seleccionado no pertenece "
                "a esta orden de trabajo."
            )

        if self.empleado_id:
            if not self.empleado.activo:
                errores["empleado"] = (
                    "El empleado asignado debe estar activo."
                )

            if self.empleado.cargo != Empleado.Cargo.MECANICO:
                errores["empleado"] = (
                    "El empleado asignado debe tener el cargo de mecánico."
                )

        if (
            self.estado == self.Estado.EN_PROCESO
            and not self.fecha_inicio
        ):
            errores["fecha_inicio"] = (
                "Un servicio en proceso debe tener fecha de inicio."
            )

        if self.estado == self.Estado.COMPLETADO:
            if not self.fecha_inicio:
                errores["fecha_inicio"] = (
                    "Un servicio completado debe tener fecha de inicio."
                )

            if not self.fecha_finalizacion:
                errores["fecha_finalizacion"] = (
                    "Un servicio completado debe tener fecha de finalización."
                )

        if (
            self.fecha_inicio
            and self.fecha_finalizacion
            and self.fecha_finalizacion < self.fecha_inicio
        ):
            errores["fecha_finalizacion"] = (
                "La fecha de finalización no puede ser anterior "
                "a la fecha de inicio."
            )

        if errores:
            raise ValidationError(errores)

    def calcular_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.subtotal = self.calcular_subtotal()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.orden.numero_orden} - "
            f"{self.servicio.nombre}"
        )
    

class RecomendacionMantenimiento(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADA = "COMPLETADA", "Completada"
        CANCELADA = "CANCELADA", "Cancelada"

    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.CASCADE,
        related_name="recomendaciones_mantenimiento",
    )

    orden_origen = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.SET_NULL,
        related_name="recomendaciones_mantenimiento",
        null=True,
        blank=True,
    )

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.SET_NULL,
        related_name="recomendaciones_mantenimiento",
        null=True,
        blank=True,
    )

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        related_name="recomendaciones_creadas",
        null=True,
        blank=True,
    )

    titulo = models.CharField(
        max_length=150,
    )

    descripcion = models.TextField(
        blank=True,
    )

    fecha_recomendada = models.DateField(
        null=True,
        blank=True,
    )

    kilometraje_recomendado = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    fecha_realizacion = models.DateTimeField(
        null=True,
        blank=True,
    )

    visible_cliente = models.BooleanField(
        default=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "estado",
            "fecha_recomendada",
            "kilometraje_recomendado",
        ]
        verbose_name = "Recomendación de mantenimiento"
        verbose_name_plural = "Recomendaciones de mantenimiento"
        indexes = [
            models.Index(
                fields=["vehiculo", "estado"],
                name="recomend_vehiculo_estado_idx",
            ),
        ]

    def clean(self):
        errores = {}

        if not self.fecha_recomendada and not self.kilometraje_recomendado:
            errores["fecha_recomendada"] = (
                "Debes indicar una fecha recomendada, un kilometraje "
                "recomendado o ambos."
            )

        if (
            self.orden_origen_id
            and self.vehiculo_id
            and self.orden_origen.vehiculo_id != self.vehiculo_id
        ):
            errores["orden_origen"] = (
                "La orden seleccionada no pertenece al vehículo indicado."
            )

        if self.empleado_id and not self.empleado.activo:
            errores["empleado"] = (
                "El empleado que registra la recomendación debe estar activo."
            )

        if (
            self.kilometraje_recomendado is not None
            and self.vehiculo_id
            and self.kilometraje_recomendado
            <= self.vehiculo.kilometraje_actual
        ):
            errores["kilometraje_recomendado"] = (
                "El kilometraje recomendado debe ser mayor "
                "al kilometraje actual del vehículo."
            )

        if (
            self.estado == self.Estado.COMPLETADA
            and not self.fecha_realizacion
        ):
            errores["fecha_realizacion"] = (
                "Una recomendación completada debe registrar "
                "la fecha de realización."
            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        if self.estado == self.Estado.COMPLETADA:
            if not self.fecha_realizacion:
                self.fecha_realizacion = timezone.now()
        else:
            self.fecha_realizacion = None

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.vehiculo.placa} - "
            f"{self.titulo}"
        )