from django.contrib.auth import get_user_model
from rest_framework import serializers

from django.db import transaction
from django.utils import timezone

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

Usuario = get_user_model()

class RegistroClienteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirmacion = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    identificacion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    direccion = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirmacion",
            "identificacion",
            "telefono",
            "direccion",
        )
        read_only_fields = ("id",)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        password = attrs.get("password")
        confirmacion = attrs.pop("password_confirmacion", None)

        if password != confirmacion:
            raise serializers.ValidationError(
                {
                    "password_confirmacion": (
                        "Las contraseñas no coinciden."
                    )
                }
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        identificacion = validated_data.pop(
            "identificacion",
            None,
        )
        telefono = validated_data.pop(
            "telefono",
            "",
        )
        direccion = validated_data.pop(
            "direccion",
            "",
        )
        password = validated_data.pop("password")

        usuario = Usuario.objects.create_user(
            password=password,
            rol=Usuario.Rol.CLIENTE,
            **validated_data,
        )

        Cliente.objects.create(
            usuario=usuario,
            identificacion=identificacion or None,
            telefono=telefono,
            direccion=direccion,
        )

        return usuario


class UsuarioResumenSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "nombre_completo",
            "rol",
        )
        read_only_fields = fields

    def get_nombre_completo(self, obj):
        return obj.get_full_name().strip() or obj.username
    
class PerfilClienteSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumenSerializer(
        read_only=True,
    )

    class Meta:
        model = Cliente
        fields = (
            "id",
            "usuario",
            "identificacion",
            "telefono",
            "direccion",
            "activo",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = (
            "id",
            "usuario",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class ClienteSerializer(serializers.ModelSerializer):
    usuario_detalle = UsuarioResumenSerializer(
        source="usuario",
        read_only=True,
    )

    class Meta:
        model = Cliente
        fields = (
            "id",
            "usuario",
            "usuario_detalle",
            "identificacion",
            "telefono",
            "direccion",
            "activo",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = (
            "creado_en",
            "actualizado_en",
        )

    def validate_usuario(self, usuario):
        if usuario.rol != Usuario.Rol.CLIENTE:
            raise serializers.ValidationError(
                "El usuario seleccionado debe tener el rol CLIENTE."
            )

        return usuario

    def validate_telefono(self, value):
        telefono = value.strip()

        if telefono and not all(
            caracter.isdigit() or caracter in "+- "
            for caracter in telefono
        ):
            raise serializers.ValidationError(
                "El teléfono contiene caracteres no permitidos."
            )

        return telefono


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = (
            "id",
            "nombre",
            "pais_origen",
            "activa",
            "creado_en",
        )
        read_only_fields = ("creado_en",)

    def validate_nombre(self, value):
        nombre = value.strip()

        if len(nombre) < 2:
            raise serializers.ValidationError(
                "El nombre debe contener al menos 2 caracteres."
            )

        return nombre


class ModeloVehiculoSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.CharField(
        source="marca.nombre",
        read_only=True,
    )
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = ModeloVehiculo
        fields = (
            "id",
            "marca",
            "marca_nombre",
            "nombre",
            "nombre_completo",
            "tipo_vehiculo",
            "activo",
            "creado_en",
        )
        read_only_fields = (
            "creado_en",
            "nombre_completo",
        )

    def get_nombre_completo(self, obj):
        return str(obj)

    def validate_nombre(self, value):
        nombre = value.strip()

        if len(nombre) < 2:
            raise serializers.ValidationError(
                "El nombre del modelo debe contener al menos 2 caracteres."
            )

        return nombre


class VehiculoSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    cliente_nombre = serializers.SerializerMethodField()
    modelo_nombre = serializers.CharField(
        source="modelo_vehiculo.nombre",
        read_only=True,
    )
    marca_nombre = serializers.CharField(
        source="modelo_vehiculo.marca.nombre",
        read_only=True,
    )

    class Meta:
        model = Vehiculo
        fields = (
            "id",
            "cliente",
            "cliente_nombre",
            "modelo_vehiculo",
            "modelo_nombre",
            "marca_nombre",
            "placa",
            "anio",
            "color",
            "kilometraje_actual",
            "numero_chasis",
            "activo",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = (
            "creado_en",
            "actualizado_en",
        )

    def get_cliente_nombre(self, obj):
        return str(obj.cliente)

    def validate_placa(self, value):
        placa = value.strip().upper()

        if len(placa) < 5:
            raise serializers.ValidationError(
                "La placa debe contener al menos 5 caracteres."
            )

        return placa

    def validate_numero_chasis(self, value):
        if value is None:
            return value

        value = value.strip().upper()
        return value or None


class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = (
            "id",
            "nombre",
            "descripcion",
            "precio_referencial",
            "foto",
            "activo",
            "visible_publicamente",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = (
            "creado_en",
            "actualizado_en",
        )

    def validate_nombre(self, value):
        nombre = value.strip()

        if len(nombre) < 3:
            raise serializers.ValidationError(
                "El nombre debe contener al menos 3 caracteres."
            )

        return nombre
    
##SERIALIZERS QUE PERMITEN LA COMUNICACIONENTRE LA CITA DEL CLIENTE Y LA RESPUESTA DEL TALLER 

class CitaSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )
    cliente_nombre = serializers.SerializerMethodField()
    vehiculo_placa = serializers.CharField(
        source="vehiculo.placa",
        read_only=True,
    )
    servicio_nombre = serializers.CharField(
        source="servicio.nombre",
        read_only=True,
    )
    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True,
    )

    class Meta:
        model = Cita
        fields = (
            "id",
            "cliente",
            "cliente_nombre",
            "vehiculo",
            "vehiculo_placa",
            "servicio",
            "servicio_nombre",
            "fecha_solicitada",
            "motivo",
            "observaciones_cliente",
            "respuesta_taller",
            "motivo_cancelacion",
            "estado",
            "estado_display",
            "creado_en",
            "actualizado_en",
            
        )
        read_only_fields = (
            "cliente",
            "respuesta_taller",
            "estado",
            "creado_en",
            "actualizado_en",
        )

    def get_cliente_nombre(self, obj):
        return str(obj.cliente)

    def validate_fecha_solicitada(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha de la cita debe ser futura."
            )

        return value

    def validate_vehiculo(self, vehiculo):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return vehiculo

        usuario = request.user

        if (
            usuario.rol == Usuario.Rol.CLIENTE
            and vehiculo.cliente.usuario_id != usuario.id
        ):
            raise serializers.ValidationError(
                "No puedes agendar una cita para un vehículo ajeno."
            )

        return vehiculo

    def validate_servicio(self, servicio):
        if servicio and (
            not servicio.activo
            or not servicio.visible_publicamente
        ):
            raise serializers.ValidationError(
                "El servicio seleccionado no está disponible."
            )

        return servicio
    
class ResponderCitaSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(
        choices=[
            Cita.Estado.CONFIRMADA,
            Cita.Estado.REPROGRAMADA,
        ]
    )

    respuesta_taller = serializers.CharField()

    fecha_solicitada = serializers.DateTimeField(
        required=False,
    )

    def validate(self, attrs):
        estado = attrs["estado"]

        if (
            estado == Cita.Estado.REPROGRAMADA
            and "fecha_solicitada" not in attrs
        ):
            raise serializers.ValidationError(
                {
                    "fecha_solicitada":
                    "Debe indicar una nueva fecha."
                }
            )

        return attrs
    
class CancelarCitaSerializer(serializers.Serializer):
    motivo_cancelacion = serializers.CharField(
        required=False,
        allow_blank=True,
    )

class RegistrarAsistenciaSerializer(
    serializers.Serializer
):
    asistio = serializers.BooleanField()


    
##ESPECIALIDAD
class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = (
            "id",
            "nombre",
            "descripcion",
            "activa",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = (
            "creado_en",
            "actualizado_en",
        )

    def validate_nombre(self, value):
        nombre = value.strip()

        if len(nombre) < 3:
            raise serializers.ValidationError(
                "El nombre debe contener al menos 3 caracteres."
            )

        return nombre
    
class EmpleadoSerializer(serializers.ModelSerializer):
    usuario_detalle = UsuarioResumenSerializer(
        source="usuario",
        read_only=True,
    )

    especialidades_detalle = EspecialidadSerializer(
        source="especialidades",
        many=True,
        read_only=True,
    )

    nombre_completo = serializers.CharField(
        read_only=True,
    )

    cargo_display = serializers.CharField(
        source="get_cargo_display",
        read_only=True,
    )

    class Meta:
        model = Empleado
        fields = (
            "id",
            "usuario",
            "usuario_detalle",
            "nombre_completo",
            "cargo",
            "cargo_display",
            "telefono",
            "fecha_ingreso",
            "especialidades",
            "especialidades_detalle",
            "activo",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = (
            "creado_en",
            "actualizado_en",
        )

    def validate_usuario(self, usuario):
        if usuario.rol != Usuario.Rol.EMPLEADO:
            raise serializers.ValidationError(
                "El usuario debe tener el rol EMPLEADO."
            )

        return usuario

    def validate(self, attrs):
        cargo = attrs.get(
            "cargo",
            getattr(self.instance, "cargo", None),
        )

        especialidades = attrs.get("especialidades")

        if (
            cargo
            and cargo != Empleado.Cargo.MECANICO
            and especialidades
        ):
            raise serializers.ValidationError(
                {
                    "especialidades": (
                        "Solo los empleados con cargo MECANICO "
                        "deberían tener especialidades técnicas."
                    )
                }
            )

        return attrs
    
class HistorialEstadoOrdenSerializer(serializers.ModelSerializer):
    estado_anterior_display = serializers.SerializerMethodField()
    estado_nuevo_display = serializers.CharField(
        source="get_estado_nuevo_display",
        read_only=True,
    )

    empleado_nombre = serializers.SerializerMethodField()

    class Meta:
        model = HistorialEstadoOrden
        fields = (
            "id",
            "orden",
            "estado_anterior",
            "estado_anterior_display",
            "estado_nuevo",
            "estado_nuevo_display",
            "titulo",
            "descripcion",
            "visible_cliente",
            "empleado",
            "empleado_nombre",
            "creado_en",
        )
        read_only_fields = fields

    def get_estado_anterior_display(self, obj):
        if not obj.estado_anterior:
            return None

        return dict(
            OrdenTrabajo.Estado.choices,
        ).get(
            obj.estado_anterior,
            obj.estado_anterior,
        )

    def get_empleado_nombre(self, obj):
        if not obj.empleado:
            return None

        return obj.empleado.nombre_completo
    

class DetalleServicioOrdenSerializer(
    serializers.ModelSerializer
):
    orden_numero = serializers.CharField(
        source="orden.numero_orden",
        read_only=True,
    )

    vehiculo_placa = serializers.CharField(
        source="orden.vehiculo.placa",
        read_only=True,
    )

    servicio_nombre = serializers.CharField(
        source="servicio.nombre",
        read_only=True,
    )

    diagnostico_titulo = serializers.CharField(
        source="diagnostico.titulo",
        read_only=True,
        default=None,
    )

    empleado_nombre = serializers.SerializerMethodField()

    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True,
    )

    class Meta:
        model = DetalleServicioOrden
        fields = (
            "id",
            "orden",
            "orden_numero",
            "vehiculo_placa",
            "servicio",
            "servicio_nombre",
            "diagnostico",
            "diagnostico_titulo",
            "empleado",
            "empleado_nombre",
            "descripcion",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "estado",
            "estado_display",
            "visible_cliente",
            "fecha_inicio",
            "fecha_finalizacion",
            "creado_en",
            "actualizado_en",
        )

        read_only_fields = (
            "empleado",
            "subtotal",
            "creado_en",
            "actualizado_en",
        )

    def get_empleado_nombre(self, obj):
        if not obj.empleado:
            return None

        return obj.empleado.nombre_completo

    def validate_orden(self, orden):
        if orden.estado in {
            OrdenTrabajo.Estado.ENTREGADO,
            OrdenTrabajo.Estado.CANCELADO,
        }:
            raise serializers.ValidationError(
                "No se pueden agregar servicios a una orden "
                "entregada o cancelada."
            )

        return orden

    def validate_cantidad(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "La cantidad debe ser mayor o igual a uno."
            )

        return value

    def validate(self, attrs):
        instance = self.instance

        orden = attrs.get(
            "orden",
            getattr(instance, "orden", None),
        )

        diagnostico = attrs.get(
            "diagnostico",
            getattr(instance, "diagnostico", None),
        )

        estado = attrs.get(
            "estado",
            getattr(
                instance,
                "estado",
                DetalleServicioOrden.Estado.PROPUESTO,
            ),
        )

        fecha_inicio = attrs.get(
            "fecha_inicio",
            getattr(instance, "fecha_inicio", None),
        )

        fecha_finalizacion = attrs.get(
            "fecha_finalizacion",
            getattr(instance, "fecha_finalizacion", None),
        )

        if (
            diagnostico
            and orden
            and diagnostico.orden_id != orden.id
        ):
            raise serializers.ValidationError(
                {
                    "diagnostico": (
                        "El diagnóstico seleccionado no pertenece "
                        "a esta orden."
                    )
                }
            )

        if (
            diagnostico
            and diagnostico.requiere_autorizacion
            and diagnostico.estado_respuesta
            != Diagnostico.EstadoRespuesta.APROBADO
            and estado
            in {
                DetalleServicioOrden.Estado.AUTORIZADO,
                DetalleServicioOrden.Estado.EN_PROCESO,
                DetalleServicioOrden.Estado.COMPLETADO,
            }
        ):
            raise serializers.ValidationError(
                {
                    "estado": (
                        "El diagnóstico debe estar aprobado antes "
                        "de autorizar o ejecutar este servicio."
                    )
                }
            )

        if estado == DetalleServicioOrden.Estado.EN_PROCESO:
            if not fecha_inicio:
                attrs["fecha_inicio"] = timezone.now()

        if estado == DetalleServicioOrden.Estado.COMPLETADO:
            if not fecha_inicio:
                attrs["fecha_inicio"] = timezone.now()

            if not fecha_finalizacion:
                attrs["fecha_finalizacion"] = timezone.now()

        if (
            fecha_inicio
            and fecha_finalizacion
            and fecha_finalizacion < fecha_inicio
        ):
            raise serializers.ValidationError(
                {
                    "fecha_finalizacion": (
                        "La fecha de finalización no puede ser "
                        "anterior a la fecha de inicio."
                    )
                }
            )

        return attrs


class OrdenTrabajoSerializer(serializers.ModelSerializer):
    vehiculo_placa = serializers.CharField(
        source="vehiculo.placa",
        read_only=True,
    )

    cliente_id = serializers.IntegerField(
        source="vehiculo.cliente_id",
        read_only=True,
    )

    cliente_nombre = serializers.SerializerMethodField()

    empleado_recepciona_nombre = serializers.SerializerMethodField()
    empleado_responsable_nombre = serializers.SerializerMethodField()

    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True,
    )
    historial_estados = HistorialEstadoOrdenSerializer(
        many=True,
        read_only=True,
    )

    detalles_servicios = DetalleServicioOrdenSerializer(
        many=True,
        read_only=True,
    )

    
    class Meta:
        model = OrdenTrabajo
        fields = (
            "id",
            "numero_orden",
            "vehiculo",
            "vehiculo_placa",
            "cliente_id",
            "cliente_nombre",
            "cita",
            "empleado_recepciona",
            "empleado_recepciona_nombre",
            "empleado_responsable",
            "empleado_responsable_nombre",
            "estado",
            "estado_display",
            "motivo_ingreso",
            "observaciones_recepcion",
            "kilometraje_ingreso",
            "fecha_ingreso",
            "fecha_estimada_entrega",
            "fecha_entrega",
            "subtotal",
            "descuento",
            "total",
            "activo",
            "historial_estados",
            "creado_en",
            "actualizado_en",
            "detalles_servicios",
        )

        read_only_fields = (
            "numero_orden",
            "total",
            "historial_estados",
            "creado_en",
            "actualizado_en",
            "detalles_servicios",
        )

    def get_cliente_nombre(self, obj):
        return str(obj.vehiculo.cliente)

    def get_empleado_recepciona_nombre(self, obj):
        return obj.empleado_recepciona.nombre_completo

    def get_empleado_responsable_nombre(self, obj):
        if not obj.empleado_responsable:
            return None

        return obj.empleado_responsable.nombre_completo

    def validate(self, attrs):
        instance = self.instance

        vehiculo = attrs.get(
            "vehiculo",
            getattr(instance, "vehiculo", None),
        )

        cita = attrs.get(
            "cita",
            getattr(instance, "cita", None),
        )

        empleado_recepciona = attrs.get(
            "empleado_recepciona",
            getattr(instance, "empleado_recepciona", None),
        )

        empleado_responsable = attrs.get(
            "empleado_responsable",
            getattr(instance, "empleado_responsable", None),
        )

        estado = attrs.get(
            "estado",
            getattr(
                instance,
                "estado",
                OrdenTrabajo.Estado.RECIBIDO,
            ),
        )

        fecha_ingreso = attrs.get(
            "fecha_ingreso",
            getattr(instance, "fecha_ingreso", timezone.now()),
        )

        fecha_estimada_entrega = attrs.get(
            "fecha_estimada_entrega",
            getattr(instance, "fecha_estimada_entrega", None),
        )

        fecha_entrega = attrs.get(
            "fecha_entrega",
            getattr(instance, "fecha_entrega", None),
        )

        subtotal = attrs.get(
            "subtotal",
            getattr(instance, "subtotal", 0),
        )

        descuento = attrs.get(
            "descuento",
            getattr(instance, "descuento", 0),
        )

        if cita and vehiculo and cita.vehiculo_id != vehiculo.id:
            raise serializers.ValidationError(
                {
                    "cita": (
                        "La cita seleccionada no pertenece "
                        "al vehículo de esta orden."
                    )
                }
            )

        if (
            empleado_recepciona
            and not empleado_recepciona.activo
        ):
            raise serializers.ValidationError(
                {
                    "empleado_recepciona": (
                        "El empleado que recibe debe estar activo."
                    )
                }
            )

        if empleado_responsable:
            if not empleado_responsable.activo:
                raise serializers.ValidationError(
                    {
                        "empleado_responsable": (
                            "El empleado responsable debe estar activo."
                        )
                    }
                )

            if empleado_responsable.cargo != Empleado.Cargo.MECANICO:
                raise serializers.ValidationError(
                    {
                        "empleado_responsable": (
                            "El empleado responsable debe tener "
                            "el cargo MECANICO."
                        )
                    }
                )

        if (
            fecha_estimada_entrega
            and fecha_estimada_entrega < fecha_ingreso.date()
        ):
            raise serializers.ValidationError(
                {
                    "fecha_estimada_entrega": (
                        "La fecha estimada no puede ser anterior "
                        "a la fecha de ingreso."
                    )
                }
            )

        if descuento > subtotal:
            raise serializers.ValidationError(
                {
                    "descuento": (
                        "El descuento no puede superar el subtotal."
                    )
                }
            )

        if estado == OrdenTrabajo.Estado.ENTREGADO:
            if not fecha_entrega:
                attrs["fecha_entrega"] = timezone.now()

        elif fecha_entrega:
            raise serializers.ValidationError(
                {
                    "fecha_entrega": (
                        "Solo una orden con estado ENTREGADO "
                        "puede tener fecha de entrega."
                    )
                }
            )

        return attrs
    

class DiagnosticoSerializer(serializers.ModelSerializer):
    orden_numero = serializers.CharField(
        source="orden.numero_orden",
        read_only=True,
    )

    vehiculo_placa = serializers.CharField(
        source="orden.vehiculo.placa",
        read_only=True,
    )

    empleado_nombre = serializers.SerializerMethodField()

    gravedad_display = serializers.CharField(
        source="get_gravedad_display",
        read_only=True,
    )

    estado_respuesta_display = serializers.CharField(
        source="get_estado_respuesta_display",
        read_only=True,
    )

    class Meta:
        model = Diagnostico
        fields = (
            "id",
            "orden",
            "orden_numero",
            "vehiculo_placa",
            "empleado",
            "empleado_nombre",
            "titulo",
            "descripcion",
            "gravedad",
            "gravedad_display",
            "requiere_autorizacion",
            "estado_respuesta",
            "estado_respuesta_display",
            "comentario_cliente",
            "fecha_respuesta",
            "visible_cliente",
            "activo",
            "creado_en",
            "actualizado_en",
        )

        read_only_fields = (
            "empleado",
            "estado_respuesta",
            "comentario_cliente",
            "fecha_respuesta",
            "creado_en",
            "actualizado_en",
        )

    def get_empleado_nombre(self, obj):
        return obj.empleado.nombre_completo

    def validate_orden(self, orden):
        if orden.estado in {
            OrdenTrabajo.Estado.ENTREGADO,
            OrdenTrabajo.Estado.CANCELADO,
        }:
            raise serializers.ValidationError(
                "No se pueden agregar diagnósticos a una orden "
                "entregada o cancelada."
            )

        return orden

    def validate_titulo(self, value):
        titulo = value.strip()

        if len(titulo) < 5:
            raise serializers.ValidationError(
                "El título debe contener al menos 5 caracteres."
            )

        return titulo

    def validate_descripcion(self, value):
        descripcion = value.strip()

        if len(descripcion) < 10:
            raise serializers.ValidationError(
                "La descripción debe contener al menos 10 caracteres."
            )

        return descripcion


class RespuestaDiagnosticoSerializer(serializers.Serializer):
    respuesta = serializers.ChoiceField(
        choices=[
            Diagnostico.EstadoRespuesta.APROBADO,
            Diagnostico.EstadoRespuesta.RECHAZADO,
        ],
    )

    comentario = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
    )
    

class RecomendacionMantenimientoSerializer(
    serializers.ModelSerializer
):
    vehiculo_placa = serializers.CharField(
        source="vehiculo.placa",
        read_only=True,
    )

    orden_numero = serializers.CharField(
        source="orden_origen.numero_orden",
        read_only=True,
        default=None,
    )

    servicio_nombre = serializers.CharField(
        source="servicio.nombre",
        read_only=True,
        default=None,
    )

    empleado_nombre = serializers.SerializerMethodField()

    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True,
    )

    class Meta:
        model = RecomendacionMantenimiento
        fields = (
            "id",
            "vehiculo",
            "vehiculo_placa",
            "orden_origen",
            "orden_numero",
            "servicio",
            "servicio_nombre",
            "empleado",
            "empleado_nombre",
            "titulo",
            "descripcion",
            "fecha_recomendada",
            "kilometraje_recomendado",
            "estado",
            "estado_display",
            "fecha_realizacion",
            "visible_cliente",
            "activo",
            "creado_en",
            "actualizado_en",
        )

        read_only_fields = (
            "empleado",
            "fecha_realizacion",
            "creado_en",
            "actualizado_en",
        )

    def get_empleado_nombre(self, obj):
        if not obj.empleado:
            return None

        return obj.empleado.nombre_completo

    def validate_titulo(self, value):
        titulo = value.strip()

        if len(titulo) < 5:
            raise serializers.ValidationError(
                "El título debe contener al menos 5 caracteres."
            )

        return titulo

    def validate(self, attrs):
        instance = self.instance

        vehiculo = attrs.get(
            "vehiculo",
            getattr(instance, "vehiculo", None),
        )

        orden_origen = attrs.get(
            "orden_origen",
            getattr(instance, "orden_origen", None),
        )

        fecha_recomendada = attrs.get(
            "fecha_recomendada",
            getattr(instance, "fecha_recomendada", None),
        )

        kilometraje_recomendado = attrs.get(
            "kilometraje_recomendado",
            getattr(instance, "kilometraje_recomendado", None),
        )

        estado = attrs.get(
            "estado",
            getattr(
                instance,
                "estado",
                RecomendacionMantenimiento.Estado.PENDIENTE,
            ),
        )

        if not fecha_recomendada and not kilometraje_recomendado:
            raise serializers.ValidationError(
                {
                    "fecha_recomendada": (
                        "Debes indicar una fecha recomendada, "
                        "un kilometraje recomendado o ambos."
                    )
                }
            )

        if (
            orden_origen
            and vehiculo
            and orden_origen.vehiculo_id != vehiculo.id
        ):
            raise serializers.ValidationError(
                {
                    "orden_origen": (
                        "La orden seleccionada no pertenece "
                        "al vehículo indicado."
                    )
                }
            )

        if (
            kilometraje_recomendado is not None
            and vehiculo
            and kilometraje_recomendado
            <= vehiculo.kilometraje_actual
        ):
            raise serializers.ValidationError(
                {
                    "kilometraje_recomendado": (
                        "El kilometraje recomendado debe ser mayor "
                        "al kilometraje actual del vehículo."
                    )
                }
            )

        if estado == RecomendacionMantenimiento.Estado.COMPLETADA:
            attrs["fecha_realizacion"] = timezone.now()

        return attrs
    
class CompletarRecomendacionSerializer(serializers.Serializer):
    kilometraje_actual = serializers.IntegerField(
        required=False,
        min_value=0,
    )

class OrdenHistorialVehiculoSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True,
    )

    empleado_responsable_nombre = serializers.SerializerMethodField()
    diagnosticos = serializers.SerializerMethodField()
    servicios_realizados = serializers.SerializerMethodField()

    class Meta:
        model = OrdenTrabajo
        fields = (
            "id",
            "numero_orden",
            "estado",
            "estado_display",
            "motivo_ingreso",
            "observaciones_recepcion",
            "kilometraje_ingreso",
            "fecha_ingreso",
            "fecha_estimada_entrega",
            "fecha_entrega",
            "subtotal",
            "descuento",
            "total",
            "empleado_responsable_nombre",
            "diagnosticos",
            "servicios_realizados",
        )

        read_only_fields = fields

    def get_empleado_responsable_nombre(self, obj):
        if not obj.empleado_responsable:
            return None

        return obj.empleado_responsable.nombre_completo

    def get_diagnosticos(self, obj):
        request = self.context.get("request")
        diagnosticos = obj.diagnosticos.filter(
            activo=True,
        )

        if (
            request
            and request.user.is_authenticated
            and request.user.rol == Usuario.Rol.CLIENTE
        ):
            diagnosticos = diagnosticos.filter(
                visible_cliente=True,
            )

        return DiagnosticoSerializer(
            diagnosticos,
            many=True,
            context=self.context,
        ).data

    def get_servicios_realizados(self, obj):
        request = self.context.get("request")

        detalles = obj.detalles_servicios.exclude(
            estado__in=[
                DetalleServicioOrden.Estado.RECHAZADO,
                DetalleServicioOrden.Estado.CANCELADO,
            ],
        )

        if (
            request
            and request.user.is_authenticated
            and request.user.rol == Usuario.Rol.CLIENTE
        ):
            detalles = detalles.filter(
                visible_cliente=True,
            )

        return DetalleServicioOrdenSerializer(
            detalles,
            many=True,
            context=self.context,
        ).data


class HistorialVehiculoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.SerializerMethodField()

    marca_nombre = serializers.CharField(
        source="modelo_vehiculo.marca.nombre",
        read_only=True,
    )

    modelo_nombre = serializers.CharField(
        source="modelo_vehiculo.nombre",
        read_only=True,
    )

    ordenes_entregadas = serializers.SerializerMethodField()
    recomendaciones = serializers.SerializerMethodField()
    resumen = serializers.SerializerMethodField()

    class Meta:
        model = Vehiculo
        fields = (
            "id",
            "placa",
            "anio",
            "color",
            "kilometraje_actual",
            "numero_chasis",
            "cliente_nombre",
            "marca_nombre",
            "modelo_nombre",
            "resumen",
            "ordenes_entregadas",
            "recomendaciones",
        )

        read_only_fields = fields

    def get_cliente_nombre(self, obj):
        return str(obj.cliente)

    def get_ordenes_entregadas(self, obj):
        ordenes = (
            obj.ordenes
            .filter(
                estado=OrdenTrabajo.Estado.ENTREGADO,
                activo=True,
            )
            .select_related(
                "empleado_responsable__usuario",
            )
            .prefetch_related(
                "diagnosticos__empleado__usuario",
                "detalles_servicios__servicio",
                "detalles_servicios__diagnostico",
                "detalles_servicios__empleado__usuario",
            )
            .order_by("-fecha_entrega", "-fecha_ingreso")
        )

        return OrdenHistorialVehiculoSerializer(
            ordenes,
            many=True,
            context=self.context,
        ).data

    def get_recomendaciones(self, obj):
        request = self.context.get("request")

        recomendaciones = (
            obj.recomendaciones_mantenimiento
            .filter(activo=True)
            .select_related(
                "orden_origen",
                "servicio",
                "empleado__usuario",
            )
            .order_by(
                "estado",
                "fecha_recomendada",
                "kilometraje_recomendado",
            )
        )

        if (
            request
            and request.user.is_authenticated
            and request.user.rol == Usuario.Rol.CLIENTE
        ):
            recomendaciones = recomendaciones.filter(
                visible_cliente=True,
            )

        return RecomendacionMantenimientoSerializer(
            recomendaciones,
            many=True,
            context=self.context,
        ).data

    def get_resumen(self, obj):
        ordenes_entregadas = obj.ordenes.filter(
            estado=OrdenTrabajo.Estado.ENTREGADO,
            activo=True,
        )

        ultima_orden = ordenes_entregadas.order_by(
            "-fecha_entrega",
            "-fecha_ingreso",
        ).first()

        proxima_recomendacion = (
            obj.recomendaciones_mantenimiento
            .filter(
                estado=RecomendacionMantenimiento.Estado.PENDIENTE,
                activo=True,
            )
            .order_by(
                "fecha_recomendada",
                "kilometraje_recomendado",
                "creado_en",
            )
            .first()
        )

        return {
            "total_mantenimientos": ordenes_entregadas.count(),
            "ultima_orden": (
                ultima_orden.numero_orden
                if ultima_orden
                else None
            ),
            "fecha_ultimo_mantenimiento": (
                ultima_orden.fecha_entrega
                if ultima_orden
                else None
            ),
            "proxima_recomendacion": (
                {
                    "id": proxima_recomendacion.id,
                    "titulo": proxima_recomendacion.titulo,
                    "fecha_recomendada": (
                        proxima_recomendacion.fecha_recomendada
                    ),
                    "kilometraje_recomendado": (
                        proxima_recomendacion
                        .kilometraje_recomendado
                    ),
                }
                if proxima_recomendacion
                else None
            ),
        }
    
class DiagnosticoSeguimientoSerializer(serializers.ModelSerializer):
    gravedad_display = serializers.CharField(
        source="get_gravedad_display",
        read_only=True,
    )

    estado_respuesta_display = serializers.CharField(
        source="get_estado_respuesta_display",
        read_only=True,
    )

    class Meta:
        model = Diagnostico
        fields = (
            "id",
            "titulo",
            "descripcion",
            "gravedad",
            "gravedad_display",
            "requiere_autorizacion",
            "estado_respuesta",
            "estado_respuesta_display",
            "comentario_cliente",
            "fecha_respuesta",
            "creado_en",
        )

        read_only_fields = fields


class ServicioSeguimientoSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(
        source="servicio.nombre",
        read_only=True,
    )

    empleado_nombre = serializers.SerializerMethodField()

    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True,
    )

    class Meta:
        model = DetalleServicioOrden
        fields = (
            "id",
            "servicio",
            "servicio_nombre",
            "descripcion",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "estado",
            "estado_display",
            "empleado_nombre",
            "fecha_inicio",
            "fecha_finalizacion",
        )

        read_only_fields = fields

    def get_empleado_nombre(self, obj):
        if not obj.empleado:
            return None

        return obj.empleado.nombre_completo


class SeguimientoOrdenSerializer(serializers.ModelSerializer):
    vehiculo = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()

    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True,
    )

    empleado_responsable_nombre = serializers.SerializerMethodField()

    progreso_porcentaje = serializers.SerializerMethodField()
    requiere_respuesta_cliente = serializers.SerializerMethodField()

    historial = serializers.SerializerMethodField()
    diagnosticos = serializers.SerializerMethodField()
    servicios = serializers.SerializerMethodField()

    class Meta:
        model = OrdenTrabajo
        fields = (
            "id",
            "numero_orden",
            "vehiculo",
            "cliente_nombre",
            "estado",
            "estado_display",
            "progreso_porcentaje",
            "requiere_respuesta_cliente",
            "motivo_ingreso",
            "observaciones_recepcion",
            "kilometraje_ingreso",
            "fecha_ingreso",
            "fecha_estimada_entrega",
            "fecha_entrega",
            "empleado_responsable_nombre",
            "subtotal",
            "descuento",
            "total",
            "historial",
            "diagnosticos",
            "servicios",
        )

        read_only_fields = fields

    def get_vehiculo(self, obj):
        return {
            "id": obj.vehiculo_id,
            "placa": obj.vehiculo.placa,
            "marca": obj.vehiculo.modelo_vehiculo.marca.nombre,
            "modelo": obj.vehiculo.modelo_vehiculo.nombre,
            "anio": obj.vehiculo.anio,
            "color": obj.vehiculo.color,
        }

    def get_cliente_nombre(self, obj):
        return str(obj.vehiculo.cliente)

    def get_empleado_responsable_nombre(self, obj):
        if not obj.empleado_responsable:
            return None

        return obj.empleado_responsable.nombre_completo

    def get_progreso_porcentaje(self, obj):
        progreso_por_estado = {
            OrdenTrabajo.Estado.RECIBIDO: 10,
            OrdenTrabajo.Estado.EN_REVISION: 25,
            OrdenTrabajo.Estado.ESPERANDO_AUTORIZACION: 40,
            OrdenTrabajo.Estado.EN_REPARACION: 65,
            OrdenTrabajo.Estado.EN_LAVADO: 85,
            OrdenTrabajo.Estado.LISTO: 100,
            OrdenTrabajo.Estado.ENTREGADO: 100,
            OrdenTrabajo.Estado.CANCELADO: 0,
        }

        return progreso_por_estado.get(
            obj.estado,
            0,
        )

    def get_requiere_respuesta_cliente(self, obj):
        return obj.diagnosticos.filter(
            activo=True,
            visible_cliente=True,
            requiere_autorizacion=True,
            estado_respuesta=Diagnostico.EstadoRespuesta.PENDIENTE,
        ).exists()

    def get_historial(self, obj):
        request = self.context.get("request")

        historial = obj.historial_estados.all()

        if (
            request
            and request.user.is_authenticated
            and request.user.rol == Usuario.Rol.CLIENTE
        ):
            historial = historial.filter(
                visible_cliente=True,
            )

        historial = historial.select_related(
            "empleado__usuario",
        ).order_by("creado_en")

        return HistorialEstadoOrdenSerializer(
            historial,
            many=True,
            context=self.context,
        ).data

    def get_diagnosticos(self, obj):
        request = self.context.get("request")

        diagnosticos = obj.diagnosticos.filter(
            activo=True,
        )

        if (
            request
            and request.user.is_authenticated
            and request.user.rol == Usuario.Rol.CLIENTE
        ):
            diagnosticos = diagnosticos.filter(
                visible_cliente=True,
            )

        diagnosticos = diagnosticos.select_related(
            "empleado__usuario",
        ).order_by("-creado_en")

        return DiagnosticoSeguimientoSerializer(
            diagnosticos,
            many=True,
            context=self.context,
        ).data

    def get_servicios(self, obj):
        request = self.context.get("request")

        servicios = obj.detalles_servicios.exclude(
            estado__in=[
                DetalleServicioOrden.Estado.RECHAZADO,
                DetalleServicioOrden.Estado.CANCELADO,
            ],
        )

        if (
            request
            and request.user.is_authenticated
            and request.user.rol == Usuario.Rol.CLIENTE
        ):
            servicios = servicios.filter(
                visible_cliente=True,
            )

        servicios = servicios.select_related(
            "servicio",
            "empleado__usuario",
        ).order_by("creado_en")

        return ServicioSeguimientoSerializer(
            servicios,
            many=True,
            context=self.context,
        ).data    
    
## Me permite ver el tipo de usuario autenticado 
class UsuarioAutenticadoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "nombre_completo",
            "rol",
        ]
        read_only_fields = fields

    def get_nombre_completo(self, obj):
        nombre_completo = obj.get_full_name().strip()

        if nombre_completo:
            return nombre_completo

        return obj.username
    