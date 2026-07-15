import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

import app.models  # Registra todos los modelos y resuelve relaciones declarativas.
from app.api.v1.endpoints import auth, users
from app.core.database import get_db, get_session
from app.core.dependencies import get_current_user_admin
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.user_audit import UserAuditAction, UserAuditLog
from app.models.user_invitation import UserInvitation
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
        tenant_one = Tenant(name="Tenant Uno", code="tenant-one", is_active=True)
        tenant_two = Tenant(name="Tenant Dos", code="tenant-two", is_active=True)
        session.add(tenant_one)
        session.add(tenant_two)
        session.commit()
        session.refresh(tenant_one)
        session.refresh(tenant_two)

        platform_admin = User(
            email="platform@example.com",
            username="platform",
            full_name="Admin Plataforma",
            hashed_password=pwd_context.hash("Admin123"),
            role=UserRole.PLATFORM_ADMIN,
            is_platform_admin=True,
            tenant_id=None,
        )
        tenant_admin = User(
            email="admin.one@example.com",
            username="admin-one",
            full_name="Admin Uno",
            hashed_password=pwd_context.hash("Admin123"),
            role=UserRole.TENANT_ADMIN,
            tenant_id=tenant_one.id,
        )
        other_admin = User(
            email="admin.two@example.com",
            username="admin-two",
            full_name="Admin Dos",
            hashed_password=pwd_context.hash("Admin123"),
            role=UserRole.TENANT_ADMIN,
            tenant_id=tenant_two.id,
        )
        inactive_user = User(
            email="inactive@example.com",
            username="inactive",
            full_name="Usuario Inactivo",
            hashed_password=pwd_context.hash("Inactive123"),
            role=UserRole.OPERATOR,
            tenant_id=tenant_one.id,
            is_active=False,
        )
        session.add(platform_admin)
        session.add(tenant_admin)
        session.add(other_admin)
        session.add(inactive_user)
        session.commit()
        for item in (platform_admin, tenant_admin, other_admin, inactive_user):
            session.refresh(item)

        current_user = {"value": tenant_admin}
        app = FastAPI()
        app.include_router(users.router, prefix="/users")
        app.include_router(auth.router, prefix="/auth")

        def override_session():
            yield session

        def override_current_admin():
            return current_user["value"]

        app.dependency_overrides[get_session] = override_session
        app.dependency_overrides[get_db] = override_session
        app.dependency_overrides[get_current_user_admin] = override_current_admin

        with TestClient(app) as client:
            yield {
                "client": client,
                "session": session,
                "current_user": current_user,
                "tenant_one": tenant_one,
                "tenant_two": tenant_two,
                "platform_admin": platform_admin,
                "tenant_admin": tenant_admin,
                "other_admin": other_admin,
                "inactive_user": inactive_user,
            }


def test_tenant_admin_only_lists_own_tenant(test_context):
    response = test_context["client"].get("/users/?page=1&page_size=100")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {item["tenant_id"] for item in response.json()["items"]} == {
        test_context["tenant_one"].id
    }


def test_tenant_admin_cannot_read_other_tenant_user(test_context):
    response = test_context["client"].get(
        f"/users/{test_context['other_admin'].id}"
    )

    assert response.status_code == 404


def test_tenant_admin_cannot_create_platform_admin(test_context):
    response = test_context["client"].post(
        "/users/",
        json={
            "email": "forbidden@example.com",
            "username": "forbidden-platform",
            "full_name": "Escalamiento",
            "password": "Secure123",
            "role": "PLATFORM_ADMIN",
            "tenant_id": test_context["tenant_one"].id,
        },
    )

    assert response.status_code == 403


def test_tenant_id_is_forced_for_tenant_admin(test_context):
    response = test_context["client"].post(
        "/users/",
        json={
            "email": "operator@example.com",
            "username": "operator-one",
            "full_name": "Operador Uno",
            "password": "Secure123",
            "role": "OPERATOR",
            "tenant_id": test_context["tenant_two"].id,
        },
    )

    assert response.status_code == 201
    assert response.json()["tenant_id"] == test_context["tenant_one"].id


def test_admin_cannot_deactivate_self(test_context):
    response = test_context["client"].patch(
        f"/users/{test_context['tenant_admin'].id}/status",
        json={"is_active": False},
    )

    assert response.status_code == 400
    assert "propia cuenta" in response.json()["detail"]


def test_platform_cannot_deactivate_last_tenant_admin(test_context):
    test_context["current_user"]["value"] = test_context["platform_admin"]

    response = test_context["client"].patch(
        f"/users/{test_context['other_admin'].id}/status",
        json={"is_active": False},
    )

    assert response.status_code == 400
    assert "último administrador" in response.json()["detail"]


def test_inactive_user_cannot_login(test_context):
    response = test_context["client"].post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "Inactive123"},
    )

    assert response.status_code == 401


def test_non_admin_dependency_is_rejected(test_context):
    operator = test_context["inactive_user"]
    operator.is_active = True

    with pytest.raises(HTTPException) as exception:
        get_current_user_admin(operator)

    assert exception.value.status_code == 403


def test_create_user_writes_safe_audit_event(test_context):
    response = test_context["client"].post(
        "/users/",
        json={
            "email": "audited@example.com",
            "username": "audited-user",
            "full_name": "Usuario Auditado",
            "password": "Secure123",
            "role": "OPERATOR",
            "tenant_id": test_context["tenant_two"].id,
        },
    )

    assert response.status_code == 201
    event = test_context["session"].query(UserAuditLog).filter(
        UserAuditLog.target_user_id == response.json()["id"]
    ).one()
    assert event.action == UserAuditAction.CREATED
    assert event.actor_user_id == test_context["tenant_admin"].id
    assert event.tenant_id == test_context["tenant_one"].id
    assert "password" not in event.changes
    assert "hashed_password" not in event.changes


def test_password_reset_audit_never_contains_secret(test_context):
    target = test_context["inactive_user"]
    response = test_context["client"].post(
        f"/users/{target.id}/reset-password",
        json={"password": "Changed123"},
    )

    assert response.status_code == 204
    event = test_context["session"].query(UserAuditLog).filter(
        UserAuditLog.target_user_id == target.id,
        UserAuditLog.action == UserAuditAction.PASSWORD_RESET,
    ).one()
    assert event.changes == {}
    assert "Changed123" not in str(event.changes)


def test_tenant_admin_only_reads_own_audit(test_context):
    session = test_context["session"]
    session.add(UserAuditLog(
        tenant_id=test_context["tenant_one"].id,
        actor_user_id=test_context["tenant_admin"].id,
        target_user_id=test_context["inactive_user"].id,
        action=UserAuditAction.UPDATED,
        changes={"full_name": {"old": "A", "new": "B"}},
    ))
    session.add(UserAuditLog(
        tenant_id=test_context["tenant_two"].id,
        actor_user_id=test_context["other_admin"].id,
        target_user_id=test_context["other_admin"].id,
        action=UserAuditAction.UPDATED,
        changes={"full_name": {"old": "C", "new": "D"}},
    ))
    session.commit()

    response = test_context["client"].get("/users/audit?page_size=100")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["tenant_id"] == test_context["tenant_one"].id


def create_invitation(test_context, suffix="one"):
    return test_context["client"].post(
        "/users/invitations",
        json={
            "email": f"invited-{suffix}@example.com",
            "username": f"invited-{suffix}",
            "full_name": "Usuario Invitado",
            "role": "OPERATOR",
            "tenant_id": test_context["tenant_two"].id,
        },
    )


def test_invitation_stores_hash_and_forces_tenant(test_context):
    response = create_invitation(test_context)

    assert response.status_code == 201
    assert response.json()["tenant_id"] == test_context["tenant_one"].id
    token = response.json()["invitation_url"].split("token=", 1)[1]
    invitation = test_context["session"].get(UserInvitation, response.json()["id"])
    assert invitation.token_hash != token
    assert len(invitation.token_hash) == 64


def test_invitation_is_single_use_and_creates_active_user(test_context):
    invitation_response = create_invitation(test_context, "accept")
    token = invitation_response.json()["invitation_url"].split("token=", 1)[1]

    accepted = test_context["client"].post(
        "/users/invitations/accept",
        json={"token": token, "password": "Accepted123"},
    )
    repeated = test_context["client"].post(
        "/users/invitations/accept",
        json={"token": token, "password": "Accepted123"},
    )

    assert accepted.status_code == 200
    assert accepted.json()["is_active"] is True
    assert accepted.json()["tenant_id"] == test_context["tenant_one"].id
    assert repeated.status_code == 400
    audit = test_context["session"].query(UserAuditLog).filter(
        UserAuditLog.target_user_id == accepted.json()["id"],
        UserAuditLog.action == UserAuditAction.INVITATION_ACCEPTED,
    ).one()
    assert "password" not in audit.changes


def test_tenant_admin_cannot_invite_platform_admin(test_context):
    response = test_context["client"].post(
        "/users/invitations",
        json={
            "email": "invite-platform@example.com",
            "username": "invite-platform",
            "full_name": "Plataforma",
            "role": "PLATFORM_ADMIN",
            "tenant_id": test_context["tenant_one"].id,
        },
    )

    assert response.status_code == 403
