
# Sistema de Gestión para Taller Mecánico - API REST

## Descripción

API REST desarrollada con **Django** y **Django REST Framework** para la gestión integral de un taller mecánico.

El sistema permite administrar clientes, vehículos, citas, órdenes de trabajo, diagnósticos, servicios realizados, recomendaciones de mantenimiento y el seguimiento completo de las reparaciones.

La API fue diseñada para ser consumida por:

* Aplicación Web (React).
* Aplicación móvil (Flutter).
* Panel de administración de Django.

---

# Objetivo

Diseñar, desarrollar y desplegar una API REST utilizando Django y Django REST Framework (DRF), conectada a PostgreSQL, aplicando buenas prácticas de desarrollo, autenticación basada en JWT, documentación técnica y despliegue en un servidor VPS.

---

# Tecnologías utilizadas

## Backend

* Python 3.13+
* Django
* Django REST Framework
* PostgreSQL
* JWT (SimpleJWT)
* UV (gestor de paquetes)

## Base de datos

* PostgreSQL

## Despliegue

* Gunicorn
* Nginx
* Linux VPS

## Documentación

* DRF Spectacular (Swagger / OpenAPI)

---

# Librerías utilizadas

## Dependencias principales

```text
Django
djangorestframework
djangorestframework-simplejwt
psycopg
python-decouple
Pillow
django-cors-headers
drf-spectacular
gunicorn
```

## Instalación de dependencias

```bash
uv sync
```

O manualmente:

```bash
uv add django
uv add djangorestframework
uv add djangorestframework-simplejwt
uv add psycopg
uv add python-decouple
uv add Pillow
uv add django-cors-headers
uv add drf-spectacular
uv add gunicorn
```

---

# Instalación del proyecto

## Clonar repositorio

```bash
git clone https://github.com/Roman2018122/DjangoRest-TallerApi.git
```

```bash
cd DjangoRest-TallerApi.git
```

---

## Crear entorno virtual

```bash
uv sync
```

---

## Variables de entorno

Crear un archivo:

```text
.env
```

Ejemplo:

```env
SECRET_KEY=TU_SECRET_KEY

DEBUG=True

ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=taller_mecanico
DB_USER=taller_user
DB_PASSWORD=taller_pass
DB_HOST=localhost
DB_PORT=5432
```

---

## Ejecutar migraciones

```bash
uv run python manage.py migrate
```

---

## Crear superusuario

```bash
uv run python manage.py createsuperuser
```

---

## Ejecutar servidor

```bash
uv run python manage.py runserver
```

---

# Autenticación JWT

## Obtener token

```
POST /api/token/
```

Ejemplo

```json
{
    "username":"usuario",
    "password":"password"
}
```

Respuesta

```json
{
    "access":"TOKEN",
    "refresh":"TOKEN"
}
```

---

## Renovar token

```
POST /api/token/refresh/
```

```json
{
    "refresh":"TOKEN"
}
```

---

# Roles del sistema

## Cliente

Puede:

* Registrarse.
* Iniciar sesión.
* Gestionar sus vehículos.
* Agendar citas.
* Consultar órdenes.
* Aprobar diagnósticos.
* Consultar historial.
* Consultar recomendaciones.
* Consultar seguimiento.

---

## Empleado

Puede:

* Gestionar órdenes.
* Crear diagnósticos.
* Registrar servicios.
* Actualizar estados.
* Registrar recomendaciones.

---

## Administrador

Acceso completo al sistema.

---

# Funcionalidades implementadas

## Clientes

* Registro.
* Login.
* Perfil.

---

## Vehículos

* Registro.
* Consulta.
* Historial.

---

## Citas

* Crear.
* Consultar.
* Actualizar.

---

## Órdenes de trabajo

* Recepción.
* Cambio de estados.
* Responsable.
* Totales.
* Entrega.

---

## Historial de estados

Registro automático de cada cambio realizado en una orden.

---

## Diagnósticos

* Registro.
* Solicitud de autorización.
* Aprobación o rechazo por el cliente.

---

## Servicios realizados

* Asociación a la orden.
* Costos.
* Estados.
* Fechas.

---

## Recomendaciones

* Próximo mantenimiento.
* Próximo kilometraje.
* Seguimiento.

---

## Historial del vehículo

Incluye:

* Órdenes anteriores.
* Diagnósticos.
* Servicios realizados.
* Recomendaciones.
* Último mantenimiento.

---

## Seguimiento de reparación

Permite visualizar en tiempo real:

* Estado actual.
* Progreso.
* Diagnósticos.
* Servicios.
* Historial de estados.

---

# Flujo del sistema

```text
Cliente

↓

Registro

↓

Vehículo

↓

Cita

↓

Recepción

↓

Orden de trabajo

↓

Diagnóstico

↓

Autorización del cliente

↓

Servicio

↓

Entrega

↓

Historial

↓

Recomendaciones
```

---

# Endpoints principales

## Autenticación

```
POST /api/token/
POST /api/token/refresh/
```

---

## Clientes

```
/api/clientes/
```

---

## Vehículos

```
/api/vehiculos/
```

---

## Citas

```
/api/citas/
```

---

## Órdenes

```
/api/ordenes-trabajo/
```

---

## Diagnósticos

```
/api/diagnosticos/
```

---

## Servicios realizados

```
/api/detalles-servicios/
```

---

## Recomendaciones

```
/api/recomendaciones-mantenimiento/
```

---

## Seguimiento

```
GET /api/ordenes-trabajo/{id}/seguimiento/
```

---

## Historial

```
GET /api/vehiculos/{id}/historial/
```

---

# Panel administrativo

```
/admin/
```

---

# Documentación de la API

Swagger

```
/api/docs/
```

OpenAPI

```
/api/schema/
```

ReDoc

```
/api/redoc/
```

---

# Despliegue

El proyecto está preparado para ejecutarse en un servidor Linux utilizando:

* Gunicorn como servidor WSGI.
* Nginx como proxy inverso.
* PostgreSQL como base de datos.
* Variables de entorno mediante `.env`.

---

# Autor

Proyecto desarrollado por Jonathan Torres como parte de la asignatura de Desarrollo de Aplicaciones con Django REST Framework.
