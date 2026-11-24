"""Tests de integración para endpoints de procesos, dashboard y expediente."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine
from datetime import datetime

import app.models
from app.api.v1.endpoints import auth, processes, workflows, dashboard
from app.core.database import get_session
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.client import Client
from app.models.obligation import Obligation, ObligationStatus, ObligationType
from app.models.process import CobroProcess, ProcessHistory, ProcessStatus
from app.models.workflow import WorkflowState, WorkflowTransition, WorkflowStateCode
from app.repositories.user import pwd_context


@pytest.fixture()
def test_context():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        tenant = Tenant(name="Test Tenant", code="test-tenant", is_active=True)
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

        admin = User(
            email="admin@test.com",
            username="admin",
            full_name="Admin Test",
            hashed_password=pwd_context.hash("Admin123"),
            role=UserRole.TENANT_ADMIN,
            tenant_id=tenant.id,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)

        # Crear estados de workflow
        state1 = WorkflowState(
            tenant_id=tenant.id,
            code=WorkflowStateCode.CARTERA_CARGADA,
            name="Cartera Cargada",
            description="Estado inicial",
            order=1,
            max_days=30,
        )
        state2 = WorkflowState(
            tenant_id=tenant.id,
            code=WorkflowStateCode.OBLIGACION_VALIDADA,
            name="Obligación Validada",
            description="Obligación verificada",
            order=2,
            max_days=15,
        )
        state3 = WorkflowState(
            tenant_id=tenant.id,
            code=WorkflowStateCode.PAGADO,
            name="Pagado",
            description="Proceso finalizado",
            order=20,
            is_final=True,
        )
        session.add_all([state1, state2, state3])
        session.commit()
        session.refresh(state1)
        session.refresh(state2)
        session.refresh(state3)

        # Crear transición
        transition = WorkflowTransition(
            tenant_id=tenant.id,
            source_state_id=state1.id,
            target_state_id=state2.id,
            name="Validar",
            is_automatic=False,
            is_active=True,
        )
        session.add(transition)
        session.commit()

        # Crear cliente
        client = Client(
            tenant_id=tenant.id,
            identification="123456789",
            name="Cliente Test",
            email="cliente@test.com",
            phone="3001234567",
        )
        session.add(client)
        session.commit()
        session.refresh(client)

        # Crear obligación
        obligation = Obligation(
            amount=1000000.0,
            currency="COP",
            due_date=datetime(2025, 12, 31),
            issue_date=datetime(2025, 1, 1),
            status=ObligationStatus.pending,
            type=ObligationType.invoice,
            description="Obligación test",
            client_id=client.id,
        )
        session.add(obligation)
        session.commit()
        session.refresh(obligation)

        # Crear proceso
        process = CobroProcess(
            tenant_id=tenant.id,
            reference="REF-001",
            observation="Proceso de prueba",
            current_state_id=state1.id,
            status=ProcessStatus.ACTIVE,
        )
        session.add(process)
        session.commit()
        session.refresh(process)

        obligation.process_id = process.id
        session.add(obligation)
        session.commit()

        yield {
            "engine": engine,
            "session": session,
            "tenant": tenant,
            "admin": admin,
            "client": client,
            "obligation": obligation,
            "process": process,
            "state1": state1,
            "state2": state2,
            "state3": state3,
        }


@pytest.fixture()
def client(test_context):
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(processes.router, prefix="/api/v1/processes")
    app.include_router(workflows.router, prefix="/api/v1/workflows")
    app.include_router(dashboard.router, prefix="/api/v1/dashboard")

    def override_get_session():
        with Session(test_context["engine"]) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def _login(client: TestClient) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


class TestProcessEndpoints:
    def test_get_processes_paginated(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/processes/", headers=headers, params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_process_detail(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        pid = test_context["process"].id
        resp = client.get(f"/api/v1/processes/{pid}/detail", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["reference"] == "REF-001"
        assert "available_transitions" in data

    def test_get_process_stats(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/processes/stats", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_processes"] >= 1
        assert data["active_processes"] >= 1

    def test_get_process_timeline(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        pid = test_context["process"].id
        resp = client.get(f"/api/v1/processes/{pid}/timeline", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_expedient(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        pid = test_context["process"].id
        resp = client.get(f"/api/v1/processes/{pid}/expedient", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["process"]["reference"] == "REF-001"
        assert data["client_name"] == "Cliente Test"
        assert len(data["obligations"]) >= 1

    def test_create_and_get_notes(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        pid = test_context["process"].id

        # Crear nota
        resp = client.post(f"/api/v1/processes/{pid}/notes", headers=headers, json={
            "title": "Nota de prueba",
            "content": "Contenido de la nota de gestión",
            "note_type": "gestion",
        })
        assert resp.status_code == 200
        note = resp.json()
        assert note["title"] == "Nota de prueba"
        assert note["note_type"] == "gestion"

        # Listar notas
        resp = client.get(f"/api/v1/processes/{pid}/notes", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_process_documents(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        pid = test_context["process"].id
        resp = client.get(f"/api/v1/processes/{pid}/documents", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestDashboardEndpoints:
    def test_get_dashboard_stats(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/dashboard/stats", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_clients"] >= 1
        assert data["processes_in_progress"] >= 1
        assert "state_distribution" in data
        assert "top_debtors" in data


class TestWorkflowEndpoints:
    def test_get_states(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/workflows/states/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 3

    def test_get_transitions(self, client, test_context):
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/workflows/transitions/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
