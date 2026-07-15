from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CitaViewSet,
    ClienteViewSet,
    EmpleadoViewSet,
    EspecialidadViewSet,
    HistorialEstadoOrdenViewSet,
    MarcaViewSet,
    MiPerfilClienteView,
    ModeloVehiculoViewSet,
    OrdenTrabajoViewSet,
    RegistroClienteView,
    ServicioViewSet,
    VehiculoViewSet,
    DiagnosticoViewSet,  
    DetalleServicioOrdenViewSet,
    RecomendacionMantenimientoViewSet,
)

router = DefaultRouter()

router.register(
    "detalles-servicios",
    DetalleServicioOrdenViewSet,
    basename="detalle-servicio",
)

router.register(
    "recomendaciones-mantenimiento",
    RecomendacionMantenimientoViewSet,
    basename="recomendacion-mantenimiento",
)

router.register(
    "clientes",
    ClienteViewSet,
    basename="cliente",
)

router.register(
    "marcas",
    MarcaViewSet,
    basename="marca",
)

router.register(
    "modelos-vehiculo",
    ModeloVehiculoViewSet,
    basename="modelo-vehiculo",
)

router.register(
    "vehiculos",
    VehiculoViewSet,
    basename="vehiculo",
)

router.register(
    "servicios",
    ServicioViewSet,
    basename="servicio",
)

router.register(
    "citas",
    CitaViewSet,
    basename="cita",
)

router.register(
    "especialidades",
    EspecialidadViewSet,
    basename="especialidad",
)

router.register(
    "empleados",
    EmpleadoViewSet,
    basename="empleado",
)

router.register(
    "ordenes-trabajo",
    OrdenTrabajoViewSet,
    basename="orden-trabajo",
)

router.register(
    "historial-estados",
    HistorialEstadoOrdenViewSet,
    basename="historial-estado",
)

router.register(
    "diagnosticos",
    DiagnosticoViewSet,
    basename="diagnostico",
)

urlpatterns = [
    path(
        "registro/",
        RegistroClienteView.as_view(),
        name="registro-cliente",
    ),
    path(
        "mi-perfil/",
        MiPerfilClienteView.as_view(),
        name="mi-perfil-cliente",
    ),
]

urlpatterns += router.urls