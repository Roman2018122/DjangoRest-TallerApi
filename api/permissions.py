from rest_framework.permissions import SAFE_METHODS, BasePermission
from .models import Cliente

class IsAdminOrReadOnly(BasePermission):
    """
    Permite GET, HEAD y OPTIONS a cualquier usuario.

    Para crear, actualizar o eliminar exige un usuario administrativo.
    """

    message = (
        "Solo el personal administrativo puede modificar este recurso."
    )

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsAdminOrEmployee(BasePermission):
    """
    Permite acceso al administrador y a los empleados del taller.
    """

    message = "Este recurso es exclusivo del personal del taller."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return (
            request.user.is_staff
            or request.user.rol in {"ADMIN", "EMPLEADO"}
        )
    
class IsOwnerOrWorkshopStaff(BasePermission):
    """
    Permite al cliente acceder únicamente a recursos de su propiedad.

    Administradores y empleados pueden acceder a todos.
    """

    message = "No tienes permiso para acceder a este recurso."

    def has_object_permission(self, request, view, obj):
        usuario = request.user

        if not usuario or not usuario.is_authenticated:
            return False

        if (
            usuario.is_staff
            or usuario.rol in {"ADMIN", "EMPLEADO"}
        ):
            return True

        if hasattr(obj, "cliente"):
            cliente = obj.cliente

            if hasattr(cliente, "usuario_id"):
                return cliente.usuario_id == usuario.id

        if isinstance(obj, Cliente):
            return obj.usuario_id == usuario.id

        return False