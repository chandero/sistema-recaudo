#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Maestro de Generación del Proyecto
Sistema de Seguimiento y Control de Cobro de Cartera
Versión: 1.0 Final
Tecnología: FastAPI, Vue3, PostgreSQL, Docker
"""

import os
import sys

# Definición de archivos y su contenido
FILES = {
    # --- BACKEND CONFIG ---
    "backend/requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pandas==2.1.4
openpyxl==3.1.2
python-docx==1.1.0
odfpy==1.4.1
jinja2==3.1.3
reportlab==4.0.9
celery==5.3.6
redis==5.0.1
httpx==0.26.0
""",

    "backend/.env": """DATABASE_URL=postgresql://postgres:postgres@db:5432/cartera_db
SECRET_KEY=tu_clave_secreta_muy_segura_cambiar_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://redis:6379/0
""",

    "backend/app/__init__.py": """# Sistema de Seguimiento y Control de Cobro de Cartera
""",

    "backend/app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine
from app.db import base  # Importar modelos para registrarlos

app = FastAPI(title="Sistema de Cobro de Cartera", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción restringir al dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def on_startup():
    # Aquí se podrían crear tablas si no se usa alembic en prod
    pass

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
""",

    "backend/app/core/config.py": """from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sistema de Cobro de Cartera"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cartera"
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"

settings = Settings()
""",

    "backend/app/core/security.py": """from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
""",

    "backend/app/db/session.py": """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",

    "backend/app/db/base.py": """# Importar todos los modelos para que Alembic los detecte
from app.models.tenant import Tenant
from app.models.user import User
from app.models.workflow import WorkflowState, WorkflowTransition
from app.models.client import Client
from app.models.obligation import Obligation
from app.models.process import Process
from app.models.document_template import DocumentTemplate
from app.models.import_log import ImportLog, ImportMappingTemplate
""",

    # --- MODELS ---
    "backend/app/models/__init__.py": "",
    
    "backend/app/models/tenant.py": """from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="tenant")
    clients = relationship("Client", back_populates="tenant")
    processes = relationship("Process", back_populates="tenant")
""",

    "backend/app/models/user.py": """from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default=UserRole.VIEWER)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="users")
""",

    "backend/app/models/workflow.py": """from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class WorkflowState(Base):
    __tablename__ = "workflow_states"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)
    max_days = Column(Integer, nullable=True)  # Días máximos en este estado
    is_final = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)  # Null = global
    
    transitions = relationship("WorkflowTransition", back_populates="source_state", foreign_keys="WorkflowTransition.source_state_id")

class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"
    
    id = Column(Integer, primary_key=True, index=True)
    source_state_id = Column(Integer, ForeignKey("workflow_states.id"))
    target_state_id = Column(Integer, ForeignKey("workflow_states.id"))
    condition_code = Column(String)  # Ej: "PAGO_CONFIRMADO", "TIEMPO_VENCIDO"
    automatic = Column(Boolean, default=False)
    delay_days = Column(Integer, default=0)
    
    source_state = relationship("WorkflowState", foreign_keys=[source_state_id], back_populates="transitions")
    target_state = relationship("WorkflowState", foreign_keys=[target_state_id])
""",

    "backend/app/models/client.py": """from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    identification = Column(String, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    city = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="clients")
    obligations = relationship("Obligation", back_populates="client")
""",

    "backend/app/models/obligation.py": """from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class Obligation(Base):
    __tablename__ = "obligations"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    number = Column(String, index=True)
    vigencia = Column(String)  # Año o periodo
    value_total = Column(Float, default=0.0)
    value_capital = Column(Float, default=0.0)
    value_interest = Column(Float, default=0.0)
    value_fines = Column(Float, default=0.0)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client", back_populates="obligations")
""",

    "backend/app/models/process.py": """from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class Process(Base):
    __tablename__ = "processes"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    obligation_id = Column(Integer, ForeignKey("obligations.id"), nullable=False)
    current_state_id = Column(Integer, ForeignKey("workflow_states.id"))
    resolution_number = Column(String, nullable=True)
    radicado_number = Column(String, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, onupdate=datetime.utcnow)
    notes = Column(Text)
    
    tenant = relationship("Tenant", back_populates="processes")
    obligation = relationship("Obligation")
    current_state = relationship("WorkflowState")
    history = relationship("ProcessHistory", back_populates="process")
""",

    "backend/app/models/document_template.py": """from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class DocumentTemplate(Base):
    __tablename__ = "document_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)  # docx, odt, pdf
    variables_schema = Column(Text)  # JSON con las variables esperadas
    version = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant")
""",

    "backend/app/models/import_log.py": """from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import json

class ImportMappingTemplate(Base):
    __tablename__ = "import_mapping_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    mapping_config = Column(Text)  # JSON: {"columna_excel": "campo_sistema"}
    created_at = Column(DateTime, default=datetime.utcnow)

class ImportLog(Base):
    __tablename__ = "import_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    file_name = Column(String)
    total_rows = Column(Integer)
    success_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    status = Column(String, default="PROCESSING")  # PROCESSING, COMPLETED, FAILED
    error_details = Column(Text)  # JSON con errores por fila
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
""",

    # --- API ROUTERS ---
    "backend/app/api/__init__.py": "",
    "backend/app/api/v1/__init__.py": "",
    "backend/app/api/v1/api.py": """from fastapi import APIRouter
from app.api.v1.endpoints import auth, tenants, users, clients, imports, documents, workflows

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
""",

    "backend/app/api/v1/endpoints/__init__.py": "",
    
    "backend/app/api/v1/endpoints/auth.py": """from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Email o contraseña incorrectos")
    if not user.active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "tenant_id": user.tenant_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": user.email, "role": user.role}}
""",

    "backend/app/api/v1/endpoints/tenants.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tenant import Tenant
from pydantic import BaseModel

router = APIRouter()

class TenantCreate(BaseModel):
    name: str
    code: str

@router.get("/")
def get_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).filter(Tenant.active == True).all()

@router.post("/")
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    if db.query(Tenant).filter(Tenant.code == tenant.code).first():
        raise HTTPException(status_code=400, detail="Código ya existe")
    db_tenant = Tenant(**tenant.dict())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant
""",

    "backend/app/api/v1/endpoints/users.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "VIEWER"
    tenant_id: int = None

@router.get("/")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role,
        tenant_id=user.tenant_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
""",

    "backend/app/api/v1/endpoints/clients.py": """from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.client import Client
from typing import List

router = APIRouter()

@router.get("/", response_model=List[dict])
def get_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # En producción filtrar por tenant_id del usuario actual
    return db.query(Client).offset(skip).limit(limit).all()
""",

    "backend/app/api/v1/endpoints/imports.py": """from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.import_log import ImportLog, ImportMappingTemplate
import pandas as pd
import io
import json

router = APIRouter()

@router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    template_name: str = Form(None),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Formato no soportado")
    
    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        columns = df.columns.tolist()
        preview = df.head(5).to_dict('records')
        
        log = ImportLog(
            file_name=file.filename,
            total_rows=len(df),
            status="PENDING_MAPPING"
        )
        db.add(log)
        db.commit()
        
        return {
            "import_id": log.id,
            "columns": columns,
            "preview": preview,
            "total_rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/")
async def process_import(
    import_id: int = Form(...),
    mapping: str = Form(...),  # JSON string
    db: Session = Depends(get_db)
):
    mapping_dict = json.loads(mapping)
    # Lógica real de procesamiento aquí
    log = db.query(ImportLog).filter(ImportLog.id == import_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Import no found")
    
    log.status = "COMPLETED"
    log.success_rows = log.total_rows # Simulado
    db.commit()
    return {"status": "success", "processed": log.total_rows}
""",

    "backend/app/api/v1/endpoints/documents.py": """from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.document_template import DocumentTemplate
import shutil
import os

router = APIRouter()

UPLOAD_DIR = "uploads/templates"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    return db.query(DocumentTemplate).all()

@router.post("/templates")
async def create_template(
    name: str = Form(...),
    code: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_ext = file.filename.split(".")[-1]
    if file_ext not in ["docx", "odt", "pdf"]:
        raise HTTPException(status_code=400, detail="Formato no soportado")
    
    file_path = f"{UPLOAD_DIR}/{code}.{file_ext}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    template = DocumentTemplate(
        name=name,
        code=code,
        file_path=file_path,
        file_type=file_ext
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template
""",

    "backend/app/api/v1/endpoints/workflows.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.workflow import WorkflowState, WorkflowTransition

router = APIRouter()

@router.get("/states")
def get_states(db: Session = Depends(get_db)):
    return db.query(WorkflowState).order_by(WorkflowState.order_index).all()

@router.get("/transitions")
def get_transitions(db: Session = Depends(get_db)):
    return db.query(WorkflowTransition).all()
""",

    # --- SEED DATA ---
    "backend/app/db/seed_workflow.py": """
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.workflow import WorkflowState, WorkflowTransition

def seed():
    db = SessionLocal()
    try:
        states_data = [
            ("CARTERA_CARGADA", "Cartera Cargada", 1),
            ("OBLIGACION_VALIDADA", "Obligación Validada", 2),
            ("PENDIENTE_ASIGNACION_RESOLUCION", "Pendiente Asignación Resolución", 3),
            ("RESOLUCION_RADICADOS_ASIGNADOS", "Resolución/Radicados Asignados", 4),
            ("DOCUMENTO_NOTIFICACION_GENERADO", "Documento Generado", 5),
            ("NOTIFICACION_ENVIADA", "Notificación Enviada", 6),
            ("ESPERANDO_RESULTADO_NOTIFICACION", "Esperando Resultado", 7, 10), # 10 días max
            ("NOTIFICACION_ENTREGADA", "Entregada", 8),
            ("NOTIFICACION_DEVUELTA", "Devuelta", 9),
            ("REINTENTO_NOTIFICACION", "Reintento", 10),
            ("ESPERANDO_PAGO_VOLUNTARIO", "Esperando Pago", 11, 15),
            ("COBRO_PERSUASIVO", "Cobro Persuasivo", 12),
            ("ACUERDO_DE_PAGO", "Acuerdo de Pago", 13),
            ("SEGUIMIENTO_ACUERDO", "Seguimiento Acuerdo", 14),
            ("ACUERDO_INCUMPLIDO", "Acuerdo Incumplido", 15),
            ("COBRO_PREJURIDICO", "Cobro Prejurídico", 16),
            ("COBRO_COACTIVO", "Cobro Coactivo", 17),
            ("PAGADO", "Pagado", 18, 0, True),
            ("ARCHIVADO", "Archivado", 19, 0, True),
            ("INCOBRABLE", "Incobrable", 20, 0, True),
        ]
        
        states = {}
        for data in states_data:
            code, name, order = data[0], data[1], data[2]
            max_days = data[3] if len(data) > 3 else None
            is_final = data[4] if len(data) > 4 else False
            
            state = WorkflowState(code=code, name=name, order_index=order, max_days=max_days, is_final=is_final)
            db.add(state)
            states[code] = state
        
        db.commit()
        print("Workflow states seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
""",

    # --- FRONTEND CONFIG ---
    "frontend/package.json": """{
  "name": "cartera-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "primevue": "^3.49.0",
    "primeicons": "^6.0.1",
    "axios": "^1.6.5",
    "chart.js": "^4.4.1",
    "primeflex": "^3.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.3",
    "vite": "^5.0.11"
  }
}
""",

    "frontend/vite.config.js": """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true
      }
    }
  }
})
""",

    "frontend/index.html": """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8">
    <link rel="icon" type="image/svg+xml" href="/vite.svg">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Cobro de Cartera</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
""",

    "frontend/src/main.js": """import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(PrimeVue, {
    theme: {
        preset: Aura
    }
})

app.mount('#app')
""",

    "frontend/src/App.vue": """<template>
  <router-view />
</template>

<script setup>
</script>

<style>
body {
  margin: 0;
  font-family: var(--font-family);
}
</style>
""",

    "frontend/src/router/index.js": """import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import AdminView from '../views/AdminView.vue'
import ClientesView from '../views/ClientesView.vue'
import ResolucionesView from '../views/ResolucionesView.vue'
import WorkflowView from '../views/WorkflowView.vue'
import EmailTemplatesView from '../views/EmailTemplatesView.vue'
import ImportarView from '../views/ImportarView.vue'
import DocumentosView from '../views/DocumentosView.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: LoginView },
  { path: '/dashboard', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/admin', component: AdminView, meta: { requiresAuth: true, role: 'PLATFORM_ADMIN' } },
  { path: '/clientes', component: ClientesView, meta: { requiresAuth: true } },
  { path: '/resoluciones', component: ResolucionesView, meta: { requiresAuth: true } },
  { path: '/workflow', component: WorkflowView, meta: { requiresAuth: true } },
  { path: '/email-templates', component: EmailTemplatesView, meta: { requiresAuth: true } },
  { path: '/importar', component: ImportarView, meta: { requiresAuth: true } },
  { path: '/documentos', component: DocumentosView, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
""",

    "frontend/src/views/LoginView.vue": """<template>
  <div class="surface-ground flex align-items-center justify-content-center min-h-screen">
    <Card class="w-full md:w-24rem">
      <template #title>Iniciar Sesión</template>
      <template #content>
        <FloatLabel variant="on">
          <InputText id="email" v-model="email" class="w-full mb-3" />
          <label for="email">Correo Electrónico</label>
        </FloatLabel>
        <FloatLabel variant="on">
          <Password id="password" v-model="password" toggleMask class="w-full mb-3" />
          <label for="password">Contraseña</label>
        </FloatLabel>
        <Button label="Ingresar" icon="pi pi-sign-in" class="w-full" @click="login" :loading="loading" />
        <p v-if="error" class="text-red-500 mt-2 text-center">{{ error }}</p>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const email = ref('admin@platform.com')
const password = ref('admin123')
const loading = ref(false)
const error = ref('')

const login = async () => {
  loading.value = true
  error.value = ''
  try {
    const formData = new FormData()
    formData.append('username', email.value)
    formData.append('password', password.value)
    
    const response = await axios.post('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    
    localStorage.setItem('token', response.data.access_token)
    localStorage.setItem('user', JSON.stringify(response.data.user))
    router.push('/dashboard')
  } catch (e) {
    error.value = 'Credenciales inválidas'
  } finally {
    loading.value = false
  }
}
</script>
""",

    "frontend/src/views/DashboardView.vue": """<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Dashboard</h1>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card v-for="i in 4" :key="i" class="text-center">
        <template #content>
          <i class="pi pi-chart-line text-4xl text-blue-500 mb-2"></i>
          <div class="text-xl font-bold">1,234</div>
          <div class="text-gray-500">Procesos Activos</div>
        </template>
      </Card>
    </div>
  </div>
</template>
""",

    "frontend/src/views/AdminView.vue": """<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Administración de Plataforma</h1>
    <TabView>
      <TabPanel header="Tenants">
        <DataTable :value="[]" paginator :rows="10">
          <Column field="name" header="Nombre"></Column>
          <Column field="code" header="Código"></Column>
          <Column header="Acciones">
            <template #body>
              <Button icon="pi pi-pencil" rounded text />
            </template>
          </Column>
        </DataTable>
        <Button label="Nuevo Tenant" icon="pi pi-plus" class="mt-3" />
      </TabPanel>
      <TabPanel header="Usuarios">
        <p>Gestión de usuarios por tenant.</p>
      </TabPanel>
    </TabView>
  </div>
</template>
""",

    "frontend/src/views/ClientesView.vue": """<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Gestión de Contribuyentes</h1>
    <DataTable :value="[]" paginator :rows="10">
      <Column field="name" header="Nombre"></Column>
      <Column field="identification" header="Identificación"></Column>
      <Column field="email" header="Email"></Column>
    </DataTable>
  </div>
</template>
""",

    "frontend/src/views/ResolucionesView.vue": """<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Asignación de Resoluciones</h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
      <Card header="Pendientes">
        <template #content><div class="text-2xl font-bold">500</div></template>
      </Card>
      <Card header="Rango Actual">
        <template #content><div class="text-2xl font-bold">2024-001 a 2024-150</div></template>
      </Card>
    </div>
    <Button label="Generar Masivo" icon="pi pi-file-pdf" severity="success" />
  </div>
</template>
""",

    "frontend/src/views/WorkflowView.vue": """<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Flujo de Cobro (Kanban)</h1>
    <ScrollPanel style="width: 100%; height: 600px">
      <div class="flex gap-4">
        <div v-for="state in states" :key="state.code" class="bg-surface-100 p-3 rounded w-64 flex-shrink-0">
          <h3 class="font-bold mb-2">{{ state.name }}</h3>
          <div class="bg-white p-2 mb-2 shadow-sm rounded border-l-4 border-blue-500">
            <small>Proc #1234</small>
          </div>
        </div>
      </div>
    </ScrollPanel>
  </div>
</template>
<script setup>
const states = [
  {code: 'CARTERA_CARGADA', name: 'Cargada'},
  {code: 'NOTIFICACION_ENVIADA', name: 'Enviada'},
  {code: 'COBRO_PERSUASIVO', name: 'Persuasivo'},
  {code: 'PAGADO', name: 'Pagado'}
]
</script>
""",

    "frontend/src/views/EmailTemplatesView.vue": """<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Plantillas de Correo</h1>
    <Textarea rows="5" cols="30" placeholder="Cuerpo del correo... {{ cliente.nombre }}" class="w-full" />
    <Button label="Guardar Plantilla" icon="pi pi-save" class="mt-2" />
  </div>
</template>
""",

    "frontend/src/views/ImportarView.vue": """<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Importar Cartera (Excel/CSV)</h1>
    <FileUpload mode="basic" accept=".xlsx,.xls,.csv" :maxFileSize="1000000" @select="onSelect" />
    
    <div v-if="columns.length" class="mt-4">
      <h3>Mapeo de Columnas</h3>
      <div v-for="col in columns" :key="col" class="flex align-items-center mb-2">
        <span class="w-32 font-bold">{{ col }}</span>
        <Dropdown :options="mappingOptions" v-model="mapping[col]" placeholder="Seleccionar campo" class="w-full ml-2" />
      </div>
      <Button label="Procesar Importación" icon="pi pi-upload" class="mt-3" @click="process" />
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const columns = ref([])
const mapping = ref({})
const mappingOptions = ['identificacion', 'nombre', 'direccion', 'valor_total', 'vigencia']

const onSelect = (event) => {
  // Simulación: en real se sube y el backend devuelve columnas
  columns.value = ['NIT', 'NOMBRE', 'DIRECCION', 'VALOR', 'PERIODO']
}
const process = () => {
  alert('Enviando a backend...')
}
</script>
""",

    "frontend/src/views/DocumentosView.vue": """<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Gestión Documental</h1>
    <TabView>
      <TabPanel header="Plantillas">
        <FileUpload mode="basic" accept=".docx,.odt,.pdf" :maxFileSize="5000000" @select="onUpload" />
        <div v-if="previewMode" class="mt-4 border p-4 bg-surface-50">
          <h3>Vista Previa</h3>
          <p>Estimado <strong>{{ cliente.nombre }}</strong>: Su deuda es <strong>${{ cliente.valor }}</strong>.</p>
          <small>Variables detectadas: {{ cliente.nombre }}, {{ cliente.valor }}</small>
        </div>
      </TabPanel>
      <TabPanel header="Generar Lote">
        <p>Seleccione procesos y genere PDFs masivos.</p>
        <Button label="Descargar ZIP" icon="pi pi-download" />
      </TabPanel>
    </TabView>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const previewMode = ref(false)
const cliente = { nombre: 'Juan Pérez', valor: '150.000' }
const onUpload = () => { previewMode.value = true }
</script>
""",

    "frontend/src/stores/auth.js": """import { defineStore } from 'pinia'
export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null, token: localStorage.getItem('token') }),
  actions: {
    logout() { this.token = null; this.user = null; localStorage.clear() }
  }
})
""",

    # --- DOCKER & INFRA ---
    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: cartera_db
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/cartera_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "8080:80"
    depends_on:
      - frontend
      - backend

volumes:
  pgdata:
  uploads:
""",

    "backend/Dockerfile": """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
""",

    "frontend/Dockerfile": """FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
EXPOSE 3000
""",

    "nginx.conf": """events {}
http {
  server {
    listen 80;
    
    location /api {
      proxy_pass http://backend:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
      proxy_pass http://frontend:3000;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection 'upgrade';
      proxy_cache_bypass $http_upgrade;
    }
  }
}
""",

    "README.md": """# Sistema de Seguimiento y Control de Cobro de Cartera

## Ejecución Rápida

1. Asegúrate de tener Docker y Docker Compose instalados.
2. Ejecuta:
   ```bash
   docker compose up -d --build
   ```
3. Inicializa la base de datos:
   ```bash
   docker compose exec backend alembic upgrade head
   docker compose exec backend python -m app.db.seed_workflow
   ```
4. Accede a:
   - Frontend: http://localhost:8080
   - API Docs: http://localhost:8080/api/docs
   - Usuario Admin: `admin@platform.com` / `admin123`

## Estructura
- `/backend`: FastAPI, SQLAlchemy, Modelos.
- `/frontend`: Vue 3, PrimeVue, Vite.
- `docker-compose.yml`: Orquestación completa.
""",

    "GUIA_INSTALACION.md": """# Guía Detallada de Instalación

## Requisitos
- Docker Desktop o Docker Engine + Compose
- 4GB RAM mínimos recomendados

## Pasos
1. Clona o genera el proyecto.
2. Ejecuta `docker compose up -d --build`.
3. Espera a que los contenedores estén `Up`.
4. Ejecuta las migraciones y seed (ver README).

## Solución de Problemas
- Si el frontend no carga, verifica logs: `docker compose logs frontend`.
- Si hay error de DB, reinicia: `docker compose restart db`.
"""
}

def create_directories():
    """Crea todos los directorios necesarios."""
    dirs = set()
    for path in FILES.keys():
        dir_path = os.path.dirname(path)
        if dir_path:
            dirs.add(dir_path)
    
    for d in sorted(dirs):
        os.makedirs(d, exist_ok=True)
        print(f"✅ Directorio creado: {d}")

def write_files():
    """Escribe o reemplaza todos los archivos."""
    for path, content in FILES.items():
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            print(f"📄 Archivo generado: {path}")
        except Exception as e:
            print(f"❌ Error escribiendo {path}: {e}")

def main():
    print("🚀 Iniciando generación del proyecto de Cobro de Cartera...")
    create_directories()
    write_files()
    print("\n✨ ¡Proyecto generado exitosamente!")
    print("👉 Sigue las instrucciones en README.md para ejecutar con Docker.")

if __name__ == "__main__":
    main()
