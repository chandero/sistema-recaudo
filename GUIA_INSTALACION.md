# Guía de Instalación y Ejecución - Sistema de Gestión de Cartera

## Requisitos Previos

- Docker y Docker Compose instalados
- Git (opcional, para clonar el repositorio)

## Estructura del Proyecto

```
/workspace
├── backend/                 # Backend FastAPI
│   ├── app/                # Código fuente
│   │   ├── api/           # Endpoints REST
│   │   ├── core/          # Configuración y seguridad
│   │   ├── models/        # Modelos SQLAlchemy
│   │   ├── schemas/       # Esquemas Pydantic
│   │   ├── services/      # Lógica de negocio
│   │   └── db/            # Seeders y configuración DB
│   ├── alembic/           # Migraciones de base de datos
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # Frontend Vue 3
│   ├── src/
│   │   ├── components/   # Componentes reutilizables
│   │   ├── views/        # Vistas principales
│   │   ├── router/       # Configuración de rutas
│   │   ├── stores/       # Estado global (Pinia)
│   │   └── services/     # Servicios API
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml     # Orquestación de contenedores
└── .env                   # Variables de entorno
```

## Instrucciones de Ejecución

### 1. Clonar/Acceder al Directorio

```bash
cd /workspace
```

### 2. Configurar Variables de Entorno (Opcional)

El archivo `.env` ya está configurado con valores por defecto. Si necesitas cambiarlos:

```bash
# Editar .env según tus necesidades
nano .env
```

Variables disponibles:
- `DB_USER`: Usuario de PostgreSQL
- `DB_PASSWORD`: Contraseña de PostgreSQL
- `DB_NAME`: Nombre de la base de datos
- `SECRET_KEY`: Clave secreta para JWT (¡cambiar en producción!)
- `REDIS_URL`: URL de Redis

### 3. Levantar los Contenedores

```bash
docker-compose up -d --build
```

Este comando:
- Construye las imágenes de backend y frontend
- Inicia PostgreSQL, Redis, backend y frontend
- Crea la red interna `cartera_network`

### 4. Ejecutar Migraciones

```bash
# Ejecutar migraciones de base de datos
docker-compose exec backend alembic upgrade head

# Ejecutar seed inicial del workflow
docker-compose exec backend python -m app.db.seed_workflow
```

### 5. Verificar Estado

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver estado de los contenedores
docker-compose ps
```

## Accesos al Sistema

### Frontend
- **URL**: http://localhost
- **Puerto**: 80

### Backend API
- **URL**: http://localhost:8000
- **Puerto**: 8000
- **Documentación Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Base de Datos PostgreSQL
- **Host**: localhost
- **Puerto**: 5432
- **Usuario**: cartera_user
- **Contraseña**: cartera_pass
- **Base de datos**: cartera_db

### Redis
- **Host**: localhost
- **Puerto**: 6379

## Usuario Inicial por Defecto

Después de ejecutar el seed, puedes usar:

**Administrador de Plataforma:**
- Email: admin@platform.com
- Password: admin123

**Usuario Tenant Demo:**
- Email: demo@tenant.com
- Password: demo123

## Comandos Útiles

### Detener el sistema
```bash
docker-compose down
```

### Detener y eliminar volúmenes (¡cuidado! borra la BD)
```bash
docker-compose down -v
```

### Reiniciar un servicio específico
```bash
docker-compose restart backend
docker-compose restart frontend
```

### Ver logs de un servicio
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

### Ejecutar comandos dentro de los contenedores
```bash
# Backend
docker-compose exec backend bash
docker-compose exec backend python -m pytest

# Frontend
docker-compose exec frontend sh

# Base de datos
docker-compose exec db psql -U cartera_user -d cartera_db
```

## Desarrollo Local (Sin Docker)

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_URL=postgresql://cartera_user:cartera_pass@localhost:5432/cartera_db
export SECRET_KEY=tu_clave_secreta

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev

# Compilar para producción
npm run build
```

## Módulos Implementados

### Backend
- ✅ Autenticación JWT
- ✅ Multi-tenant estricto
- ✅ Gestión de usuarios y roles
- ✅ Modelos de clientes, obligaciones, procesos
- ✅ Workflow configurable
- ✅ Plantillas documentales
- ✅ Historial de procesos
- ✅ Tareas y asignaciones
- ✅ Importación Excel/CSV (estructura lista)

### Frontend
- ✅ Login con autenticación
- ✅ Dashboard principal
- ✅ Administración de tenants y usuarios
- ✅ Gestión de clientes
- ✅ Vista de resoluciones y radicados
- ✅ Editor visual de workflow
- ✅ Gestión de plantillas de email
- ✅ Navegación con guardias de ruta

## Próximos Pasos

1. **Completar endpoints de importación** de Excel/CSV con mapeo dinámico
2. **Implementar generación de PDF** desde plantillas DOCX
3. **Conectar vistas frontend** con endpoints reales
4. **Agregar scheduler** para cambios automáticos de estado
5. **Implementar funciones de IA** sugeridas en el documento

## Solución de Problemas

### Error: Puerto ya en uso
```bash
# Liberar puertos
docker-compose down
# O cambiar puertos en docker-compose.yml
```

### Error: Base de datos no se conecta
```bash
# Verificar que PostgreSQL esté saludable
docker-compose logs db
# Reiniciar servicio
docker-compose restart db
```

### Error: Migraciones fallidas
```bash
# Resetear migraciones (¡cuidado! borra datos)
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head
```

### Frontend no carga
```bash
# Verificar build
docker-compose logs frontend
# Reconstruir
docker-compose up -d --build frontend
```

## Soporte

Para reportar errores o solicitar funcionalidades, consultar el documento base del proyecto o el README principal.
