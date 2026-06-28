# MoviCore

Sistema de Gestión de Transporte — API REST para gestión y monitoreo del transporte.

## Integrantes

- _[Calo Alexander]_
- _[Llumiquinga Yandri]_
- _[Tanqueño Edison]_

---

## Descripción del sistema

MoviCore es un backend modular construido con Django y Django REST Framework que expone una API RESTful para la administración de rutas, vehículos, conductores, viajes, posiciones GPS, incidentes y notificaciones del transporte público.

### Apps del proyecto

| App | Función |
|-----|---------|
| `accounts` | Usuarios, autenticación JWT, perfiles, auditoría |
| `transport` | Catálogos: rutas, paradas, vehículos, empresas, distritos, sectores |
| `operations` | Operaciones: conductores, viajes, horarios, GPS, mantenimiento |
| `incidents` | Incidentes y tipos de incidente durante viajes |
| `analytics` | Dashboard, reportes de rutas/vehículos, estado del sistema |
| `notifications` | Notificaciones por usuario y preferencias |
| `demo` | Comandos de gestión: `seed_demo`, `simulate_gps` |

### Stack técnico

- Python 3.12, Django 6.0, Django REST Framework 3.17
- PostgreSQL 16
- Autenticación JWT (SimpleJWT)
- Documentación OpenAPI 3 con Swagger UI (drf-spectacular)
- Gunicorn + Nginx

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/edtanqueno420/GestionTrasporte.git
cd GestionTrasporte
```

### 2. Crear entorno virtual e instalar dependencias

```bash
uv python install 3.12
uv venv
uv sync
```

Si no usás `uv`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_SECRET_KEY=tu-secret-key-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgres://movicore_user:movicore_pass@localhost:5432/movicore_db

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

ADMIN_URL=secure-admin/
```

Generar un `DJANGO_SECRET_KEY` seguro:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Crear la base de datos

```sql
CREATE USER movicore_user WITH PASSWORD 'movicore_pass';
CREATE DATABASE movicore_db OWNER movicore_user;
GRANT ALL PRIVILEGES ON DATABASE movicore_db TO movicore_user;
ALTER USER movicore_user CREATEDB;
```

### 5. Ejecutar migraciones

```bash
uv run python manage.py migrate
```

### 6. Crear superusuario

```bash
uv run python manage.py createsuperuser
```

### 7. (Opcional) Poblar datos de demostración

```bash
uv run python manage.py seed_demo
uv run python manage.py simulate_gps --trip_id=2
```

### 8. Ejecutar servidor de desarrollo

```bash
uv run python manage.py runserver
```

### 9. Verificar

- API: http://localhost:8000/api/auth/health/
- Swagger UI: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/secure-admin/

---

## Despliegue

### Configuración del VPS

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3.12 python3.12-venv postgresql nginx

# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Configuración de PostgreSQL

```bash
sudo -u postgres psql

CREATE USER movicore_user WITH PASSWORD 'movicore_pass';
CREATE DATABASE movicore_db OWNER movicore_user;
GRANT ALL PRIVILEGES ON DATABASE movicore_db TO movicore_user;
GRANT ALL ON SCHEMA public TO movicore_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO movicore_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO movicore_user;
ALTER USER movicore_user CREATEDB;
\q
```

### Configuración de Gunicorn

Crear archivo `/etc/systemd/system/gunicorn-movicore.service`:

```ini
[Unit]
Description=MoviCore Gunicorn service
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/GestionTrasporte
EnvironmentFile=/opt/GestionTrasporte/.env
RuntimeDirectory=gunicorn-movicore
ExecStart=/opt/GestionTrasporte/.venv/bin/gunicorn config.wsgi:application \
    --workers 3 \
    --bind unix:/run/gunicorn-movicore.sock \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log

ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID

[Install]
WantedBy=multi-user.target
```

Habilitar e iniciar:

```bash
sudo mkdir -p /var/log/gunicorn
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-movicore
```

### Configuración de Nginx

Crear archivo `/etc/nginx/sites-available/movicore`:

```nginx
upstream movicore {
    server unix:/run/gunicorn-movicore.sock;
}

server {
    listen 80;
    server_name https://tanqueno-produccion.uaeftt-ute.site/;

    client_max_body_size 10M;

    location /static/ {
        alias /opt/GestionTrasporte/staticfiles/;
    }

    location / {
        proxy_pass http://movicore;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activar sitio:

```bash
sudo ln -s /etc/nginx/sites-available/movicore /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Uso de la API

### Obtener token JWT

```bash
# Login como administrador
curl -X POST https://tanqueno-produccion.uaeftt-ute.site/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Login como conductor
curl -X POST https://tanqueno-produccion.uaeftt-ute.site/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "conductor1", "password": "demo123"}'
```

Respuesta:

```json
{
    "success": true,
    "data": {
        "access": "eyJhbGciOiJIUzI1NiIs...",
        "refresh": "eyJhbGciOiJIUzI1NiIs...",
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "Administrator"
        }
    }
}
```

### Usar endpoints protegidos

Agregar el header `Authorization: Bearer <token>`:

```bash
curl https://tanqueno-produccion.uaeftt-ute.site/api/transport/routes/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Ejemplos de peticiones

**Crear una ruta:**

```bash
curl -X POST https://tanqueno-produccion.uaeftt-ute.site/api/transport/routes/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "RUTA-001",
    "name": "Norte-Sur",
    "description": "Ruta principal"
  }'
```

**Registrar un incidente:**

```bash
curl -X POST https://tanqueno-produccion.uaeftt-ute.site/api/incidents/incidents/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "trip": 1,
    "incident_type": 1,
    "latitude": -0.22985,
    "longitude": -78.52495,
    "description": "Accidente de tránsito leve",
    "severity": "high"
  }'
```

**Consultar dashboard de analítica:**

```bash
curl https://tanqueno-produccion.uaeftt-ute.site/api/analytics/dashboard/ \
  -H "Authorization: Bearer <token>"
```

Respuesta:

```json
{
    "total_routes": 5,
    "total_vehicles": 10,
    "active_trips": 3,
    "total_incidents": 2,
    "open_incidents": 1
}
```

---

## Endpoints

### Autenticación (`/api/auth/`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `health/` | Health check del servicio | ✗ |
| POST | `login/` | Iniciar sesión (obtener JWT) | ✗ |
| POST | `refresh/` | Refrescar token JWT | ✗ |
| POST | `verify/` | Verificar validez del token | ✗ |
| POST | `register/` | Registrar nuevo usuario | ✗ |
| GET | `me/` | Obtener usuario autenticado | ✓ |
| PATCH | `profile/` | Actualizar perfil del usuario | ✓ |
| POST | `change-password/` | Cambiar contraseña | ✓ |

### Transporte (`/api/transport/`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| CRUD | `routes/` | Gestionar rutas | ✓ |
| CRUD | `bus-stops/` | Gestionar paradas | ✓ |
| CRUD | `vehicles/` | Gestionar vehículos | ✓ |
| CRUD | `transport-companies/` | Gestionar empresas de transporte | ✓ |
| CRUD | `districts/` | Gestionar distritos | ✓ |
| CRUD | `sectors/` | Gestionar sectores | ✓ |
| CRUD | `vehicle-types/` | Gestionar tipos de vehículo | ✓ |
| CRUD | `vehicle-statuses/` | Gestionar estados de vehículo | ✓ |
| CRUD | `route-bus-stops/` | Asignar paradas a rutas | ✓ |

### Operaciones (`/api/operations/`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| CRUD | `drivers/` | Gestionar conductores | ✓ |
| CRUD | `driver-assignments/` | Asignar conductores a rutas | ✓ |
| CRUD | `schedules/` | Gestionar horarios | ✓ |
| CRUD | `route-coordinates/` | Coordenadas para polylíneas de ruta | ✓ |
| CRUD | `maintenances/` | Mantenimiento de vehículos | ✓ |
| CRUD | `trips/` | Viajes realizados | ✓ |
| CRUD | `gps-positions/` | Posiciones GPS de viajes | ✓ |

### Incidentes (`/api/incidents/`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| CRUD | `incident-types/` | Gestionar tipos de incidente | ✓ |
| CRUD | `incidents/` | Gestionar incidentes | ✓ |
| POST | `incidents/<id>/resolve/` | Resolver un incidente | ✓ |

### Analítica (`/api/analytics/`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `dashboard/` | KPIs generales del sistema | ✓ |
| GET | `routes/<id>/report/` | Reporte detallado de una ruta | ✓ |
| GET | `vehicles/<id>/report/` | Reporte detallado de un vehículo | ✓ |
| GET | `status/` | Estado del sistema (público) | ✗ |

### Notificaciones (`/api/notifications/`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `notifications/` | Listar notificaciones del usuario | ✓ |
| PATCH | `notifications/<id>/read/` | Marcar como leída | ✓ |
| POST | `notifications/read_all/` | Marcar todas como leídas | ✓ |

### Público (`/api/public/`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `routes/` | Listar rutas disponibles | ✗ |
| GET | `routes/<id>/stops/` | Paradas de una ruta | ✗ |
| GET | `routes/<id>/coordinates/` | Coordenadas de una ruta (polyline) | ✗ |
| GET | `bus-stops/` | Listar paradas | ✗ |

---

## Comandos de gestión

```bash
# Poblar datos demo
uv run python manage.py seed_demo

# Simular GPS en tiempo real para un viaje
uv run python manage.py simulate_gps --trip_id=2

# Generar esquema OpenAPI
uv run python manage.py spectacular --validate

# Exportar esquema a archivo
uv run python manage.py spectacular --file schema.yml
```

## Usuarios demo (seed_demo)

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin` | `admin123` | Administrador |
| `conductor1` | `demo123` | Conductor |
| `usuario1` | `demo123` | Usuario regular |

---

## Ejecutar tests

```bash
uv run python manage.py test
```

Para tests específicos por app:

```bash
uv run python manage.py test apps.accounts
uv run python manage.py test apps.transport
uv run python manage.py test apps.operations
```

---

## Postman

La colección de Postman se encuentra en `docs/postman/quitomove_demo_collection.json`.

Importarla en Postman y configurar las variables de entorno:
- `base_url`: `https://tanqueno-produccion.uaeftt-ute.site/`
- `token`: se auto-asigna al ejecutar Login
