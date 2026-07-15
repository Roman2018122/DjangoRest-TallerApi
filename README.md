## instalaciond de dependencias 
uv add django
uv add djangorestframework
uv add djangorestframework-simplejwt
uv add "psycopg[binary]"
uv add pillow
uv add python-decouple

## Creacion de la base de datos
psql -U postgres

CREATE DATABASE taller_mecanico;

CREATE USER taller_user
WITH PASSWORD 'taller_pass';

ALTER ROLE taller_user
SET client_encoding TO 'utf8';

ALTER ROLE taller_user
SET default_transaction_isolation TO 'read committed';

ALTER ROLE taller_user
SET timezone TO 'America/Guayaquil';

GRANT ALL PRIVILEGES
ON DATABASE taller_mecanico
TO taller_user;

/c

### conceder permisos esquema publico 

GRANT ALL ON SCHEMA public TO taller_user;
ALTER SCHEMA public OWNER TO taller_user;
