from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.endpoints import auth, tenants, clients, obligations, workflows, processes, documents, importer

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(obligations.router, prefix="/obligations", tags=["Obligations"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_router.include_router(processes.router, prefix="/processes", tags=["Processes"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(importer.router, prefix="/importer", tags=["Importaciones Excel/CSV"])
