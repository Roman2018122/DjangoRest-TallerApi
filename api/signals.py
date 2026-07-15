from django.db.models.signals import post_save, pre_save,  post_delete
from django.dispatch import receiver

from .models import HistorialEstadoOrden, OrdenTrabajo, DetalleServicioOrden


TITULOS_ESTADOS = {
    OrdenTrabajo.Estado.RECIBIDO: "Vehículo recibido",
    OrdenTrabajo.Estado.EN_REVISION: "Vehículo en revisión",
    OrdenTrabajo.Estado.ESPERANDO_AUTORIZACION: (
        "Esperando autorización del cliente"
    ),
    OrdenTrabajo.Estado.EN_REPARACION: "Reparación en proceso",
    OrdenTrabajo.Estado.EN_LAVADO: "Vehículo en lavado",
    OrdenTrabajo.Estado.LISTO: "Vehículo listo para retirar",
    OrdenTrabajo.Estado.ENTREGADO: "Vehículo entregado",
    OrdenTrabajo.Estado.CANCELADO: "Orden cancelada",
}


DESCRIPCIONES_ESTADOS = {
    OrdenTrabajo.Estado.RECIBIDO: (
        "El vehículo fue recibido correctamente en el taller."
    ),
    OrdenTrabajo.Estado.EN_REVISION: (
        "El personal del taller inició la revisión del vehículo."
    ),
    OrdenTrabajo.Estado.ESPERANDO_AUTORIZACION: (
        "El taller necesita la autorización del cliente antes de continuar."
    ),
    OrdenTrabajo.Estado.EN_REPARACION: (
        "Los trabajos autorizados se encuentran en ejecución."
    ),
    OrdenTrabajo.Estado.EN_LAVADO: (
        "La reparación terminó y el vehículo se encuentra en lavado."
    ),
    OrdenTrabajo.Estado.LISTO: (
        "El vehículo está listo para ser retirado."
    ),
    OrdenTrabajo.Estado.ENTREGADO: (
        "El vehículo fue entregado al cliente."
    ),
    OrdenTrabajo.Estado.CANCELADO: (
        "La orden de trabajo fue cancelada."
    ),
}


@receiver(
    pre_save,
    sender=OrdenTrabajo,
)
def guardar_estado_anterior(sender, instance, **kwargs):
    """
    Guarda temporalmente el estado anterior antes de actualizar la orden.
    """
    if not instance.pk:
        instance._estado_anterior = None
        return

    try:
        orden_anterior = sender.objects.only(
            "estado",
        ).get(pk=instance.pk)

        instance._estado_anterior = orden_anterior.estado
    except sender.DoesNotExist:
        instance._estado_anterior = None


@receiver(
    post_save,
    sender=OrdenTrabajo,
)
def crear_historial_estado(sender, instance, created, **kwargs):
    """
    Crea el primer registro al crear una orden y registra posteriormente
    cada cambio de estado.
    """
    estado_anterior = getattr(
        instance,
        "_estado_anterior",
        None,
    )

    if not created and estado_anterior == instance.estado:
        return

    HistorialEstadoOrden.objects.create(
        orden=instance,
        estado_anterior=estado_anterior,
        estado_nuevo=instance.estado,
        titulo=TITULOS_ESTADOS.get(
            instance.estado,
            instance.get_estado_display(),
        ),
        descripcion=DESCRIPCIONES_ESTADOS.get(
            instance.estado,
            "",
        ),
        visible_cliente=True,
    )

@receiver(
    post_save,
    sender=DetalleServicioOrden,
)
def recalcular_orden_al_guardar_servicio(
    sender,
    instance,
    **kwargs,
):
    """
    Actualiza los valores de la orden cuando se crea
    o modifica un detalle de servicio.
    """
    instance.orden.recalcular_totales()


@receiver(
    post_delete,
    sender=DetalleServicioOrden,
)
def recalcular_orden_al_eliminar_servicio(
    sender,
    instance,
    **kwargs,
):
    """
    Actualiza los valores de la orden cuando se elimina
    un detalle de servicio.
    """
    instance.orden.recalcular_totales()