from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Cita,
    Cliente,
    ConsecutivoOrden,
    Empleado,
    Especialidad,
    HistorialEstadoOrden,
    Marca,
    ModeloVehiculo,
    OrdenTrabajo,
    Servicio,
    Usuario,
    Vehiculo,
    Diagnostico,
    DetalleServicioOrden,
    RecomendacionMantenimiento,
)




@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Información del taller",
            {
                "fields": (
                    "rol",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Información adicional",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "rol",
                )
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "rol",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "rol",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "identificacion",
        "telefono",
        "activo",
        "creado_en",
    )
    list_filter = ("activo",)
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
        "identificacion",
        "telefono",
    )
    list_select_related = ("usuario",)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "pais_origen",
        "activa",
    )
    list_filter = ("activa",)
    search_fields = ("nombre", "pais_origen")


@admin.register(ModeloVehiculo)
class ModeloVehiculoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "marca",
        "nombre",
        "tipo_vehiculo",
        "activo",
    )
    list_filter = (
        "tipo_vehiculo",
        "activo",
        "marca",
    )
    search_fields = (
        "nombre",
        "marca__nombre",
    )
    list_select_related = ("marca",)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "placa",
        "cliente",
        "modelo_vehiculo",
        "anio",
        "kilometraje_actual",
        "activo",
    )
    list_filter = (
        "activo",
        "anio",
        "modelo_vehiculo__marca",
    )
    search_fields = (
        "placa",
        "numero_chasis",
        "cliente__usuario__username",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
    )
    list_select_related = (
        "cliente__usuario",
        "modelo_vehiculo__marca",
    )


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "precio_referencial",
        "activo",
        "visible_publicamente",
    )
    list_filter = (
        "activo",
        "visible_publicamente",
    )
    search_fields = (
        "nombre",
        "descripcion",
    )



@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "vehiculo",
        "fecha_solicitada",
        "estado",
        "servicio",
    )
    list_filter = (
        "estado",
        "fecha_solicitada",
    )
    search_fields = (
        "cliente__usuario__username",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
        "vehiculo__placa",
        "motivo",
    )
    list_select_related = (
        "cliente__usuario",
        "vehiculo__modelo_vehiculo__marca",
        "servicio",
    )



@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nombre",
        "activa",
    )

    search_fields = (
        "nombre",
    )

    list_filter = (
        "activa",
    )


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "usuario",
        "cargo",
        "fecha_ingreso",
        "activo",
    )

    list_filter = (
        "cargo",
        "activo",
    )

    search_fields = (
        "usuario__first_name",
        "usuario__last_name",
        "usuario__username",
    )

    list_select_related = (
        "usuario",
    )

    filter_horizontal = (
        "especialidades",
    )


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):

    list_display = (
        "numero_orden",
        "vehiculo",
        "estado",
        "empleado_responsable",
        "fecha_ingreso",
        "fecha_estimada_entrega",
    )

    list_filter = (
        "estado",
        "fecha_ingreso",
    )

    search_fields = (
        "numero_orden",
        "vehiculo__placa",
    )

    autocomplete_fields = (
        "vehiculo",
        "cita",
        "empleado_recepciona",
        "empleado_responsable",
    )


@admin.register(HistorialEstadoOrden)
class HistorialEstadoOrdenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "orden",
        "estado_anterior",
        "estado_nuevo",
        "empleado",
        "visible_cliente",
        "creado_en",
    )

    list_filter = (
        "estado_nuevo",
        "visible_cliente",
        "creado_en",
    )

    search_fields = (
        "orden__numero_orden",
        "orden__vehiculo__placa",
        "titulo",
        "descripcion",
    )

    list_select_related = (
        "orden__vehiculo",
        "empleado__usuario",
    )

    readonly_fields = (
        "orden",
        "estado_anterior",
        "estado_nuevo",
        "titulo",
        "descripcion",
        "empleado",
        "visible_cliente",
        "creado_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    

@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "orden",
        "titulo",
        "gravedad",
        "requiere_autorizacion",
        "estado_respuesta",
        "empleado",
        "visible_cliente",
        "creado_en",
    )

    list_filter = (
        "gravedad",
        "requiere_autorizacion",
        "estado_respuesta",
        "visible_cliente",
        "activo",
    )

    search_fields = (
        "orden__numero_orden",
        "orden__vehiculo__placa",
        "titulo",
        "descripcion",
        "empleado__usuario__first_name",
        "empleado__usuario__last_name",
    )

    list_select_related = (
        "orden__vehiculo",
        "empleado__usuario",
    )

    readonly_fields = (
        "estado_respuesta",
        "comentario_cliente",
        "fecha_respuesta",
        "creado_en",
        "actualizado_en",
    )

@admin.register(DetalleServicioOrden)
class DetalleServicioOrdenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "orden",
        "servicio",
        "empleado",
        "cantidad",
        "precio_unitario",
        "subtotal",
        "estado",
        "visible_cliente",
    )

    list_filter = (
        "estado",
        "visible_cliente",
        "servicio",
    )

    search_fields = (
        "orden__numero_orden",
        "orden__vehiculo__placa",
        "servicio__nombre",
        "descripcion",
        "empleado__usuario__first_name",
        "empleado__usuario__last_name",
    )

    list_select_related = (
        "orden__vehiculo",
        "servicio",
        "diagnostico",
        "empleado__usuario",
    )

    readonly_fields = (
        "subtotal",
        "creado_en",
        "actualizado_en",
    )


@admin.register(RecomendacionMantenimiento)
class RecomendacionMantenimientoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vehiculo",
        "titulo",
        "servicio",
        "fecha_recomendada",
        "kilometraje_recomendado",
        "estado",
        "visible_cliente",
    )

    list_filter = (
        "estado",
        "visible_cliente",
        "activo",
        "fecha_recomendada",
    )

    search_fields = (
        "vehiculo__placa",
        "titulo",
        "descripcion",
        "orden_origen__numero_orden",
        "servicio__nombre",
    )

    list_select_related = (
        "vehiculo",
        "orden_origen",
        "servicio",
        "empleado__usuario",
    )

    readonly_fields = (
        "empleado",
        "fecha_realizacion",
        "creado_en",
        "actualizado_en",
    )