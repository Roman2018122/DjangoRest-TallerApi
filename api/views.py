from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from rest_framework import filters, generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import status

from rest_framework.views import APIView
from django.db.models import Q

from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)

from .models import (
    Cita,
    Cliente,
    Empleado,
    Especialidad,
    HistorialEstadoOrden,
    Marca,
    ModeloVehiculo,
    OrdenTrabajo,
    Servicio,
    Vehiculo,
    Diagnostico,
    DetalleServicioOrden,
    RecomendacionMantenimiento,
)
from .permissions import (
    IsAdminOrEmployee,
    IsAdminOrReadOnly,
    IsOwnerOrWorkshopStaff,
)
from .serializers import (
    DetalleServicioOrdenSerializer,
    CompletarRecomendacionSerializer,
    RecomendacionMantenimientoSerializer,
    CitaSerializer,
    ClienteSerializer,
    DiagnosticoSerializer,
    EmpleadoSerializer,
    EspecialidadSerializer,
    HistorialEstadoOrdenSerializer,
    MarcaSerializer,
    ModeloVehiculoSerializer,
    OrdenTrabajoSerializer,
    PerfilClienteSerializer,
    RegistroClienteSerializer,
    RespuestaDiagnosticoSerializer,
    ServicioSerializer,
    VehiculoSerializer,
    HistorialVehiculoSerializer,
    SeguimientoOrdenSerializer,
    UsuarioAutenticadoSerializer,


    ResponderCitaSerializer,
    CancelarCitaSerializer,
    RegistrarAsistenciaSerializer,

)

class RegistroClienteView(generics.CreateAPIView):
    serializer_class = RegistroClienteSerializer
    permission_classes = [AllowAny]

## Permite ver el peffil de usuario personalizado cliente
class MiPerfilClienteView(generics.RetrieveUpdateAPIView):
    serializer_class = PerfilClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        usuario = self.request.user

        if usuario.rol != "CLIENTE":
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Este endpoint está disponible únicamente para clientes."
            )

        try:
            return usuario.cliente
        except Cliente.DoesNotExist:
            from rest_framework.exceptions import NotFound

            raise NotFound(
                "El usuario autenticado no tiene un perfil de cliente."
            )
        
class DashboardClienteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        if usuario.rol != "CLIENTE":
            raise PermissionDenied(
                "Este recurso es exclusivo para clientes."
            )

        cliente = usuario.cliente

        data = {
            "vehiculos": Vehiculo.objects.filter(
                cliente=cliente
            ).count(),

            "citas_pendientes": Cita.objects.filter(
                cliente=cliente,
                estado__in=[
                    Cita.Estado.SOLICITADA,
                    Cita.Estado.CONFIRMADA,
                    Cita.Estado.REPROGRAMADA,
                ],
            ).count(),

            "ordenes_activas": OrdenTrabajo.objects.filter(
                vehiculo__cliente=cliente,
            ).exclude(
                estado__in=[
                    OrdenTrabajo.Estado.ENTREGADO,
                    OrdenTrabajo.Estado.CANCELADO,
                ]
            ).count(),

            "diagnosticos_pendientes": Diagnostico.objects.filter(
                orden__vehiculo__cliente=cliente,
                estado_respuesta=Diagnostico.EstadoRespuesta.PENDIENTE,
                visible_cliente=True,
            ).count(),

            "recomendaciones_pendientes": RecomendacionMantenimiento.objects.filter(
                vehiculo__cliente=cliente,
                estado=RecomendacionMantenimiento.Estado.PENDIENTE,
                visible_cliente=True,
            ).count(),
        }

        return Response(data)


class ClienteViewSet(viewsets.ModelViewSet):
    serializer_class = ClienteSerializer
    permission_classes = [IsAdminOrEmployee]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
        "identificacion",
        "telefono",
    ]
    ordering_fields = [
        "id",
        "creado_en",
        "usuario__first_name",
    ]
    ordering = ["id"]

    def get_queryset(self):
        return Cliente.objects.select_related(
            "usuario",
        ).all()


class MarcaViewSet(viewsets.ModelViewSet):
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "nombre",
        "pais_origen",
    ]
    ordering_fields = [
        "nombre",
        "creado_en",
    ]
    ordering = ["nombre"]

    def get_queryset(self):
        return Marca.objects.all()


class ModeloVehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = ModeloVehiculoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "nombre",
        "marca__nombre",
        "tipo_vehiculo",
    ]
    ordering_fields = [
        "nombre",
        "marca__nombre",
        "creado_en",
    ]
    ordering = [
        "marca__nombre",
        "nombre",
    ]

    def get_queryset(self):
        return ModeloVehiculo.objects.select_related(
            "marca",
        ).all()


class VehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = VehiculoSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrWorkshopStaff,
    ]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "placa",
        "numero_chasis",
        "modelo_vehiculo__nombre",
        "modelo_vehiculo__marca__nombre",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
    ]
    ordering_fields = [
        "placa",
        "anio",
        "kilometraje_actual",
        "creado_en",
    ]
    ordering = ["placa"]

    def get_queryset(self):
        queryset = Vehiculo.objects.select_related(
            "cliente__usuario",
            "modelo_vehiculo__marca",
        )

        usuario = self.request.user

        if usuario.rol == "CLIENTE":
            return queryset.filter(
                cliente__usuario=usuario,
            )

        return queryset

    def perform_create(self, serializer):
        usuario = self.request.user

        if usuario.rol == "CLIENTE":
            try:
                cliente = usuario.cliente
            except Cliente.DoesNotExist:
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "cliente": (
                            "El usuario no tiene un perfil de cliente."
                        )
                    }
                )

            serializer.save(cliente=cliente)
            return

        cliente_id = self.request.data.get("cliente")

        if not cliente_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "cliente": (
                        "El personal del taller debe indicar un cliente."
                    )
                }
            )

        try:
            cliente = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {"cliente": "El cliente indicado no existe."}
            )

        serializer.save(cliente=cliente)

    @action(
        detail=True,
        methods=["get"],
        url_path="historial",
        permission_classes=[IsAuthenticated],
    )
    def historial(self, request, pk=None):
        """
        Devuelve el historial consolidado del vehículo.

        Los clientes solo pueden acceder a vehículos propios porque
        get_object() utiliza el queryset filtrado del ViewSet.
        """
        vehiculo = self.get_object()

        serializer = HistorialVehiculoSerializer(
            vehiculo,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class ServicioViewSet(viewsets.ModelViewSet):
    serializer_class = ServicioSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "nombre",
        "descripcion",
    ]
    ordering_fields = [
        "nombre",
        "precio_referencial",
        "creado_en",
    ]
    ordering = ["nombre"]

    def get_queryset(self):
        queryset = Servicio.objects.all()

        usuario = self.request.user

        # En la zona pública solo se muestran servicios disponibles.
        if not usuario.is_authenticated or not usuario.is_staff:
            return queryset.filter(
                activo=True,
                visible_publicamente=True,
            )

        return queryset
    
class CitaViewSet(viewsets.ModelViewSet):
    serializer_class = CitaSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrWorkshopStaff,
    ]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "vehiculo__placa",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
        "motivo",
        "estado",
    ]
    ordering_fields = [
        "fecha_solicitada",
        "creado_en",
        "estado",
    ]
    ordering = ["-fecha_solicitada"]
    ROLES_PERSONAL_TALLER = {
        "ADMIN",
        "EMPLEADO",
    }

    def es_personal_taller(self, usuario):
        return (
            usuario.is_superuser
            or usuario.rol in self.ROLES_PERSONAL_TALLER
        )

    def get_queryset(self):
        queryset = Cita.objects.select_related(
            "cliente__usuario",
            "vehiculo__modelo_vehiculo__marca",
            "servicio",
        )

        usuario = self.request.user

        if usuario.rol == "CLIENTE":
            return queryset.filter(
                cliente__usuario=usuario,
            )

        return queryset

    def perform_create(self, serializer):
        usuario = self.request.user

        if usuario.rol == "CLIENTE":
            try:
                cliente = usuario.cliente
            except Cliente.DoesNotExist:
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "cliente": (
                            "El usuario no tiene un perfil de cliente."
                        )
                    }
                )

            vehiculo = serializer.validated_data["vehiculo"]

            if vehiculo.cliente_id != cliente.id:
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "vehiculo": (
                            "El vehículo seleccionado no te pertenece."
                        )
                    }
                )

            serializer.save(
                cliente=cliente,
                estado=Cita.Estado.SOLICITADA,
            )
            return

        cliente_id = self.request.data.get("cliente")

        if not cliente_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "cliente": (
                        "El personal del taller debe indicar un cliente."
                    )
                }
            )

        try:
            cliente = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {"cliente": "El cliente indicado no existe."}
            )

        vehiculo = serializer.validated_data["vehiculo"]

        if vehiculo.cliente_id != cliente.id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "vehiculo": (
                        "El vehículo no pertenece al cliente indicado."
                    )
                }
            )

        serializer.save(cliente=cliente)

    def update(self, request, *args, **kwargs):
        cita = self.get_object()

        if request.user.rol == "CLIENTE":
            if cita.estado not in {
                Cita.Estado.SOLICITADA,
                Cita.Estado.REPROGRAMADA,
            }:
                return Response(
                    {
                        "detail": (
                            "La cita ya no puede modificarse en su estado actual."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return super().update(request, *args, **kwargs)

##Impide que la cita pueda ser eliminada solo puede ser cancelada 

    def destroy(self, request, *args, **kwargs):
        if request.user.rol == "CLIENTE":
            return Response(
                {
                    "detail": (
                        "Las citas no se eliminan. "
                        "Utilice la opción cancelar."
                    )
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )
    
    ##Permite al usuario cliente cancelar la cita 
    
    @action(
        detail=True,
        methods=["post"],
        url_path="cancelar",
        permission_classes=[IsAuthenticated],
    )
    def cancelar(self, request, pk=None):
        cita = self.get_object()

        if cita.estado not in {
            Cita.Estado.SOLICITADA,
            Cita.Estado.CONFIRMADA,
            Cita.Estado.REPROGRAMADA,
        }:
            return Response(
                {
                    "detail": (
                        "La cita no puede cancelarse "
                        "en su estado actual."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CancelarCitaSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        cita.estado = Cita.Estado.CANCELADA
        cita.motivo_cancelacion = (
            serializer.validated_data.get(
                "motivo_cancelacion",
                "",
            )
        )

        cita.save(
            update_fields=[
                "estado",
                "motivo_cancelacion",
                "actualizado_en",
            ]
        )

        return Response(
            CitaSerializer(
                cita,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )

    ##Respuesta de citas solo personal del taller puede hacerlo 

    @action(
        detail=True,
        methods=["post"],
        url_path="responder",
        permission_classes=[IsAuthenticated],
    )
    def responder(self, request, pk=None):
        if not self.es_personal_taller(
            request.user
        ):
            return Response(
                {
                    "detail": (
                        "No tiene permiso para responder citas."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        cita = self.get_object()

        if cita.estado not in {
            Cita.Estado.SOLICITADA,
            Cita.Estado.REPROGRAMADA,
        }:
            return Response(
                {
                    "detail": (
                        "La cita no puede confirmarse "
                        "ni reprogramarse en su estado actual."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ResponderCitaSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        estado = serializer.validated_data[
            "estado"
        ]

        cita.estado = estado
        cita.respuesta_taller = (
            serializer.validated_data[
                "respuesta_taller"
            ]
        )

        update_fields = [
            "estado",
            "respuesta_taller",
            "actualizado_en",
        ]

        if estado == Cita.Estado.REPROGRAMADA:
            cita.fecha_solicitada = (
                serializer.validated_data[
                    "fecha_solicitada"
                ]
            )
            update_fields.append(
                "fecha_solicitada"
            )

        cita.save(
            update_fields=update_fields,
        )

        return Response(
            CitaSerializer(
                cita,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )
    
##Registrar asistencia del cliente a la cita 

    @action(
    detail=True,
    methods=["post"],
    url_path="registrar-asistencia",
    permission_classes=[IsAuthenticated],
    )
    def registrar_asistencia(self, request, pk=None):
        if not self.es_personal_taller(request.user):
            return Response(
                {
                    "detail": (
                        "No tiene permiso para registrar "
                        "la asistencia."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        cita = self.get_object()

        if cita.estado not in {
            Cita.Estado.CONFIRMADA,
            Cita.Estado.REPROGRAMADA,
        }:
            return Response(
                {
                    "detail": (
                        "Solo se puede registrar la asistencia "
                        "de una cita confirmada o reprogramada."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RegistrarAsistenciaSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        asistio = serializer.validated_data["asistio"]

        if asistio:
            cita.estado = Cita.Estado.ATENDIDA
        else:
            cita.estado = Cita.Estado.NO_ASISTIO

        cita.save(
            update_fields=[
                "estado",
                "actualizado_en",
            ]
        )

        return Response(
            CitaSerializer(
                cita,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )
    ##Crear orden de reparacion

    @action(
        detail=True,
        methods=["post"],
        url_path="crear-orden",
        permission_classes=[IsAuthenticated],
    )

    @transaction.atomic
    def crear_orden(
        self,
        request,
        pk=None,
    ):
        if not self.es_personal_taller(
            request.user
        ):
            return Response(
                {
                    "detail": (
                        "No tiene permiso para crear "
                        "órdenes de trabajo."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        cita = self.get_object()

        if cita.estado != Cita.Estado.ATENDIDA:
            return Response(
                {
                    "detail": (
                        "Solo se puede crear una orden "
                        "desde una cita atendida."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        orden_existente = (
            OrdenTrabajo.objects.filter(
                cita=cita,
            ).first()
        )

        if orden_existente:
            orden_serializer = (
                OrdenTrabajoSerializer(
                    orden_existente,
                    context={
                        "request": request,
                    },
                )
            )

            return Response(
                {
                    "detail": (
                        "La cita ya tiene una orden "
                        "de trabajo asociada."
                    ),
                    "orden": orden_serializer.data,
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            empleado_recepciona = (
                Empleado.objects.get(
                    usuario=request.user,
                    activo=True,
                )
            )
        except Empleado.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "El usuario autenticado no tiene "
                        "un perfil de empleado activo."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        datos_orden = request.data.copy()

        datos_orden["vehiculo"] = (
            cita.vehiculo_id
        )
        datos_orden["cita"] = cita.id
        datos_orden["empleado_recepciona"] = (
            empleado_recepciona.id
        )
        datos_orden["estado"] = (
            OrdenTrabajo.Estado.RECIBIDO
        )

        if not datos_orden.get(
            "motivo_ingreso"
        ):
            datos_orden["motivo_ingreso"] = (
                cita.motivo
            )

        serializer = OrdenTrabajoSerializer(
            data=datos_orden,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        orden = serializer.save()

        return Response(
            OrdenTrabajoSerializer(
                orden,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_201_CREATED,
    )
    


class EspecialidadViewSet(viewsets.ModelViewSet):
    serializer_class = EspecialidadSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "nombre",
        "descripcion",
    ]

    ordering_fields = [
        "nombre",
        "creado_en",
    ]

    ordering = ["nombre"]

    def get_queryset(self):
        queryset = Especialidad.objects.all()

        usuario = self.request.user

        if not usuario.is_authenticated or not usuario.is_staff:
            return queryset.filter(activa=True)

        return queryset
    
class EmpleadoViewSet(viewsets.ModelViewSet):
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAdminOrEmployee]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
        "telefono",
        "cargo",
        "especialidades__nombre",
    ]

    ordering_fields = [
        "usuario__first_name",
        "usuario__last_name",
        "cargo",
        "fecha_ingreso",
        "creado_en",
    ]

    ordering = [
        "usuario__first_name",
        "usuario__last_name",
    ]

    def get_queryset(self):
        return (
            Empleado.objects
            .select_related("usuario")
            .prefetch_related("especialidades")
            .distinct()
        )
    
class OrdenTrabajoViewSet(viewsets.ModelViewSet):
    serializer_class = OrdenTrabajoSerializer

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "numero_orden",
        "vehiculo__placa",
        "vehiculo__cliente__usuario__username",
        "vehiculo__cliente__usuario__first_name",
        "vehiculo__cliente__usuario__last_name",
        "motivo_ingreso",
        "estado",
    ]

    ordering_fields = [
        "numero_orden",
        "fecha_ingreso",
        "fecha_estimada_entrega",
        "fecha_entrega",
        "estado",
        "total",
        "creado_en",
    ]

    ordering = ["-fecha_ingreso"]

    def get_permissions(self):
        """
        Los clientes pueden consultar sus órdenes.

        Crear, modificar o eliminar órdenes está reservado
        para administradores y empleados.
        """
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminOrEmployee]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        queryset = (
            OrdenTrabajo.objects
            .select_related(
                "vehiculo__cliente__usuario",
                "vehiculo__modelo_vehiculo__marca",
                "cita",
                "empleado_recepciona__usuario",
                "empleado_responsable__usuario",
            )
            .prefetch_related(
                "historial_estados__empleado__usuario",
            )
        )

        usuario = self.request.user

        if not usuario.is_authenticated:
            return queryset.none()

        if usuario.rol == "CLIENTE":
            return queryset.filter(
                vehiculo__cliente__usuario=usuario,
            )

        return queryset

    def perform_create(self, serializer):
        usuario = self.request.user

        if usuario.rol not in {"ADMIN", "EMPLEADO"} and not usuario.is_staff:
            raise PermissionDenied(
                "Solo el personal del taller puede crear órdenes."
            )

        empleado_recepciona = serializer.validated_data.get(
            "empleado_recepciona"
        )

        if empleado_recepciona is None:
            try:
                empleado_recepciona = usuario.empleado
            except Empleado.DoesNotExist as exc:
                raise ValidationError(
                    {
                        "empleado_recepciona": (
                            "Debes indicar el empleado que recibe "
                            "el vehículo."
                        )
                    }
                ) from exc

        vehiculo = serializer.validated_data["vehiculo"]
        cita = serializer.validated_data.get("cita")

        if cita and cita.vehiculo_id != vehiculo.id:
            raise ValidationError(
                {
                    "cita": (
                        "La cita seleccionada no pertenece "
                        "al vehículo indicado."
                    )
                }
            )

        serializer.save(
            empleado_recepciona=empleado_recepciona,
        )

    def perform_update(self, serializer):
        orden = self.get_object()

        estado_anterior = orden.estado
        estado_nuevo = serializer.validated_data.get(
            "estado",
            estado_anterior,
        )

        if estado_anterior == OrdenTrabajo.Estado.ENTREGADO:
            if estado_nuevo != estado_anterior:
                raise ValidationError(
                    {
                        "estado": (
                            "Una orden entregada no puede cambiar "
                            "nuevamente de estado."
                        )
                    }
                )

        if estado_anterior == OrdenTrabajo.Estado.CANCELADO:
            if estado_nuevo != estado_anterior:
                raise ValidationError(
                    {
                        "estado": (
                            "Una orden cancelada no puede reactivarse "
                            "mediante este endpoint."
                        )
                    }
                )

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        orden = self.get_object()

        if orden.estado not in {
            OrdenTrabajo.Estado.RECIBIDO,
            OrdenTrabajo.Estado.CANCELADO,
        }:
            return Response(
                {
                    "detail": (
                        "Solo se pueden eliminar órdenes recién recibidas "
                        "o canceladas."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="seguimiento",
        permission_classes=[IsAuthenticated],
    )
    def seguimiento(self, request, pk=None):
        """
        Devuelve el seguimiento completo de una reparación.

        El cliente solo puede acceder a órdenes de sus propios vehículos
        porque get_object() utiliza el queryset filtrado del ViewSet.
        """
        orden = self.get_object()

        if (
            request.user.rol == "CLIENTE"
            and orden.estado == OrdenTrabajo.Estado.CANCELADO
        ):
            raise PermissionDenied(
                "Esta orden fue cancelada y no tiene seguimiento activo."
            )

        serializer = SeguimientoOrdenSerializer(
            orden,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class HistorialEstadoOrdenViewSet(
    viewsets.ReadOnlyModelViewSet
):
    serializer_class = HistorialEstadoOrdenSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "orden__numero_orden",
        "orden__vehiculo__placa",
        "titulo",
        "descripcion",
        "estado_anterior",
        "estado_nuevo",
    ]

    ordering_fields = [
        "creado_en",
        "estado_nuevo",
    ]

    ordering = ["creado_en"]

    def get_queryset(self):
        queryset = (
            HistorialEstadoOrden.objects
            .select_related(
                "orden__vehiculo__cliente__usuario",
                "empleado__usuario",
            )
        )

        usuario = self.request.user

        if usuario.rol == "CLIENTE":
            return queryset.filter(
                orden__vehiculo__cliente__usuario=usuario,
                visible_cliente=True,
            )

        return queryset
    

class DiagnosticoViewSet(viewsets.ModelViewSet):
    serializer_class = DiagnosticoSerializer

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "orden__numero_orden",
        "orden__vehiculo__placa",
        "titulo",
        "descripcion",
        "gravedad",
        "estado_respuesta",
    ]

    ordering_fields = [
        "creado_en",
        "gravedad",
        "estado_respuesta",
    ]

    ordering = ["-creado_en"]

    def get_permissions(self):
        if self.action in {
            "list",
            "retrieve",
            "responder",
        }:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminOrEmployee]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        queryset = (
            Diagnostico.objects
            .select_related(
                "orden__vehiculo__cliente__usuario",
                "empleado__usuario",
            )
        )

        usuario = self.request.user

        if not usuario.is_authenticated:
            return queryset.none()

        if usuario.rol == "CLIENTE":
            return queryset.filter(
                orden__vehiculo__cliente__usuario=usuario,
                visible_cliente=True,
                activo=True,
            )

        return queryset

    def perform_create(self, serializer):
        usuario = self.request.user

        try:
            empleado = usuario.empleado
        except Empleado.DoesNotExist as exc:
            raise ValidationError(
                {
                    "empleado": (
                        "El usuario autenticado no tiene un perfil "
                        "de empleado."
                    )
                }
            ) from exc

        if not empleado.activo:
            raise ValidationError(
                {
                    "empleado": (
                        "El empleado autenticado está inactivo."
                    )
                }
            )

        if empleado.cargo != Empleado.Cargo.MECANICO:
            raise ValidationError(
                {
                    "empleado": (
                        "Solo un empleado con cargo MECANICO puede "
                        "registrar diagnósticos."
                    )
                }
            )

        requiere_autorizacion = serializer.validated_data.get(
            "requiere_autorizacion",
            False,
        )

        with transaction.atomic():
            diagnostico = serializer.save(
                empleado=empleado,
                estado_respuesta=(
                    Diagnostico.EstadoRespuesta.PENDIENTE
                    if requiere_autorizacion
                    else Diagnostico.EstadoRespuesta.NO_REQUERIDA
                ),
            )

            orden = diagnostico.orden

            if (
                requiere_autorizacion
                and orden.estado
                != OrdenTrabajo.Estado.ESPERANDO_AUTORIZACION
            ):
                orden.estado = (
                    OrdenTrabajo.Estado.ESPERANDO_AUTORIZACION
                )
                orden.save(
                    update_fields=[
                        "estado",
                        "actualizado_en",
                    ]
                )

    def perform_update(self, serializer):
        diagnostico = self.get_object()

        if diagnostico.estado_respuesta in {
            Diagnostico.EstadoRespuesta.APROBADO,
            Diagnostico.EstadoRespuesta.RECHAZADO,
        }:
            raise ValidationError(
                {
                    "detail": (
                        "No se puede modificar un diagnóstico "
                        "que ya fue respondido por el cliente."
                    )
                }
            )

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        diagnostico = self.get_object()

        if diagnostico.estado_respuesta in {
            Diagnostico.EstadoRespuesta.APROBADO,
            Diagnostico.EstadoRespuesta.RECHAZADO,
        }:
            return Response(
                {
                    "detail": (
                        "No se puede eliminar un diagnóstico "
                        "que ya fue respondido."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="responder",
        permission_classes=[IsAuthenticated],
    )
    def responder(self, request, pk=None):
        diagnostico = self.get_object()
        usuario = request.user

        if usuario.rol != "CLIENTE":
            raise PermissionDenied(
                "Solo el cliente propietario puede responder "
                "este diagnóstico."
            )

        if (
            diagnostico.orden.vehiculo.cliente.usuario_id
            != usuario.id
        ):
            raise PermissionDenied(
                "Este diagnóstico no pertenece a uno de tus vehículos."
            )

        if not diagnostico.visible_cliente:
            raise PermissionDenied(
                "Este diagnóstico no está disponible para el cliente."
            )

        if not diagnostico.requiere_autorizacion:
            raise ValidationError(
                {
                    "detail": (
                        "Este diagnóstico no requiere autorización."
                    )
                }
            )

        if diagnostico.estado_respuesta != (
            Diagnostico.EstadoRespuesta.PENDIENTE
        ):
            raise ValidationError(
                {
                    "detail": (
                        "Este diagnóstico ya fue respondido."
                    )
                }
            )

        serializer = RespuestaDiagnosticoSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        respuesta = serializer.validated_data["respuesta"]
        comentario = serializer.validated_data.get(
            "comentario",
            "",
        )

        diagnostico.estado_respuesta = respuesta
        diagnostico.comentario_cliente = comentario
        diagnostico.fecha_respuesta = timezone.now()

        diagnostico.save(
            update_fields=[
                "estado_respuesta",
                "comentario_cliente",
                "fecha_respuesta",
                "actualizado_en",
            ]
        )

        return Response(
            DiagnosticoSerializer(
                diagnostico,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )

class DetalleServicioOrdenViewSet(
    viewsets.ModelViewSet
):
    serializer_class = DetalleServicioOrdenSerializer

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "orden__numero_orden",
        "orden__vehiculo__placa",
        "servicio__nombre",
        "diagnostico__titulo",
        "descripcion",
        "estado",
    ]

    ordering_fields = [
        "creado_en",
        "precio_unitario",
        "subtotal",
        "estado",
    ]

    ordering = ["creado_en"]

    def get_permissions(self):
        if self.request.method in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminOrEmployee]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        queryset = (
            DetalleServicioOrden.objects
            .select_related(
                "orden__vehiculo__cliente__usuario",
                "servicio",
                "diagnostico",
                "empleado__usuario",
            )
        )

        usuario = self.request.user

        if not usuario.is_authenticated:
            return queryset.none()

        if usuario.rol == "CLIENTE":
            return queryset.filter(
                orden__vehiculo__cliente__usuario=usuario,
                visible_cliente=True,
            )

        return queryset

    def perform_create(self, serializer):
        usuario = self.request.user

        try:
            empleado = usuario.empleado
        except Empleado.DoesNotExist as exc:
            raise ValidationError(
                {
                    "empleado": (
                        "El usuario autenticado no tiene "
                        "un perfil de empleado."
                    )
                }
            ) from exc

        if not empleado.activo:
            raise ValidationError(
                {
                    "empleado": (
                        "El empleado autenticado está inactivo."
                    )
                }
            )

        if empleado.cargo != Empleado.Cargo.MECANICO:
            raise ValidationError(
                {
                    "empleado": (
                        "Solo un mecánico puede registrar "
                        "servicios en una orden."
                    )
                }
            )

        serializer.save(
            empleado=empleado,
        )

    def perform_update(self, serializer):
        detalle = self.get_object()

        if detalle.orden.estado in {
            OrdenTrabajo.Estado.ENTREGADO,
            OrdenTrabajo.Estado.CANCELADO,
        }:
            raise ValidationError(
                {
                    "orden": (
                        "No se puede modificar un servicio de una "
                        "orden entregada o cancelada."
                    )
                }
            )

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        detalle = self.get_object()

        if detalle.estado in {
            DetalleServicioOrden.Estado.EN_PROCESO,
            DetalleServicioOrden.Estado.COMPLETADO,
        }:
            return Response(
                {
                    "detail": (
                        "No se puede eliminar un servicio "
                        "en proceso o completado."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )
    
class RecomendacionMantenimientoViewSet(
    viewsets.ModelViewSet
):
    serializer_class = RecomendacionMantenimientoSerializer

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "vehiculo__placa",
        "titulo",
        "descripcion",
        "orden_origen__numero_orden",
        "servicio__nombre",
        "estado",
    ]

    ordering_fields = [
        "fecha_recomendada",
        "kilometraje_recomendado",
        "estado",
        "creado_en",
    ]

    ordering = [
        "estado",
        "fecha_recomendada",
    ]

    def get_permissions(self):
        if self.request.method in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminOrEmployee]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        queryset = (
            RecomendacionMantenimiento.objects
            .select_related(
                "vehiculo__cliente__usuario",
                "vehiculo__modelo_vehiculo__marca",
                "orden_origen",
                "servicio",
                "empleado__usuario",
            )
        )

        usuario = self.request.user

        if not usuario.is_authenticated:
            return queryset.none()

        if usuario.rol == "CLIENTE":
            return queryset.filter(
                vehiculo__cliente__usuario=usuario,
                visible_cliente=True,
                activo=True,
            )

        return queryset

    def perform_create(self, serializer):
        usuario = self.request.user

        try:
            empleado = usuario.empleado
        except Empleado.DoesNotExist as exc:
            raise ValidationError(
                {
                    "empleado": (
                        "El usuario autenticado no tiene "
                        "un perfil de empleado."
                    )
                }
            ) from exc

        if not empleado.activo:
            raise ValidationError(
                {
                    "empleado": (
                        "El empleado autenticado está inactivo."
                    )
                }
            )

        serializer.save(
            empleado=empleado,
            estado=RecomendacionMantenimiento.Estado.PENDIENTE,
        )

    def perform_update(self, serializer):
        recomendacion = self.get_object()

        if recomendacion.estado in {
            RecomendacionMantenimiento.Estado.COMPLETADA,
            RecomendacionMantenimiento.Estado.CANCELADA,
        }:
            raise ValidationError(
                {
                    "estado": (
                        "Una recomendación completada o cancelada "
                        "no puede modificarse."
                    )
                }
            )

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        recomendacion = self.get_object()

        if recomendacion.estado == (
            RecomendacionMantenimiento.Estado.COMPLETADA
        ):
            return Response(
                {
                    "detail": (
                        "No se puede eliminar una recomendación completada."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="completar",
        permission_classes=[IsAdminOrEmployee],
    )
    def completar(self, request, pk=None):
        recomendacion = self.get_object()

        if recomendacion.estado != (
            RecomendacionMantenimiento.Estado.PENDIENTE
        ):
            raise ValidationError(
                {
                    "estado": (
                        "Solo una recomendación pendiente "
                        "puede marcarse como completada."
                    )
                }
            )

        serializer = CompletarRecomendacionSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        kilometraje_actual = serializer.validated_data.get(
            "kilometraje_actual"
        )

        with transaction.atomic():
            recomendacion.estado = (
                RecomendacionMantenimiento.Estado.COMPLETADA
            )
            recomendacion.fecha_realizacion = timezone.now()

            recomendacion.save(
                update_fields=[
                    "estado",
                    "fecha_realizacion",
                    "actualizado_en",
                ]
            )

            if kilometraje_actual is not None:
                vehiculo = recomendacion.vehiculo

                if kilometraje_actual < vehiculo.kilometraje_actual:
                    raise ValidationError(
                        {
                            "kilometraje_actual": (
                                "El nuevo kilometraje no puede ser menor "
                                "al kilometraje actual registrado."
                            )
                        }
                    )

                vehiculo.kilometraje_actual = kilometraje_actual
                vehiculo.save(
                    update_fields=[
                        "kilometraje_actual",
                        "actualizado_en",
                    ]
                )

        return Response(
            RecomendacionMantenimientoSerializer(
                recomendacion,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )



    @action(
        detail=True,
        methods=["post"],
        url_path="cancelar",
        permission_classes=[IsAdminOrEmployee],
    )
    def cancelar(self, request, pk=None):
        recomendacion = self.get_object()

        if recomendacion.estado != (
            RecomendacionMantenimiento.Estado.PENDIENTE
        ):
            raise ValidationError(
                {
                    "estado": (
                        "Solo una recomendación pendiente "
                        "puede cancelarse."
                    )
                }
            )

        recomendacion.estado = (
            RecomendacionMantenimiento.Estado.CANCELADA
        )

        recomendacion.save(
            update_fields=[
                "estado",
                "actualizado_en",
            ]
        )

        return Response(
            RecomendacionMantenimientoSerializer(
                recomendacion,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioAutenticadoSerializer(request.user)

        return Response(serializer.data)