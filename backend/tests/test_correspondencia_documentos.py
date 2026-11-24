"""
Pruebas de generación del Auto de Archivo (GD-F.03) y la Constancia Secretarial
(GD-F.01): contextos, derivación de fechas, endpoints de preview/generate,
aislamiento por tenant y envío de correo con adjuntos.
"""
import io
import smtplib
import zipfile
from datetime import date, datetime

import pytest
from docx import Document
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # Registra todos los modelos para poder crear las tablas.
from app.api.v1.endpoints import documents
from app.core.database import get_session
from app.core.dependencies import get_current_active_user
from app.models.client import Client
from app.models.document import DocumentTemplate, GeneratedDocument, TemplateType
from app.models.obligation import Obligation
from app.models.process import CobroProcess, ProcessHistory
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.workflow import WorkflowState, WorkflowStateCode
from app.services.email_service import EmailService


def _crear_plantilla_docx() -> bytes:
    """Plantilla mínima con todos los placeholders de los dos documentos."""
    documento = Document()
    documento.add_paragraph(
        "Resolución {{numero_resolucion}} de {{fecha_resolucion}}, "
        "pago {{fecha_pago}}, cuenta {{cuenta_usuario}}"
    )
    documento.add_paragraph(
        "{{nombre_usuario}} identificado con {{documento_usuario}}, "
        "dirección {{direccion_usuario}}"
    )
    documento.add_paragraph(
        "Constancia {{fecha_constancia}} — resolución "
        "{{fecha_resolucion_larga}} — en firme {{fecha_ejecutoria_larga}}"
    )
    memoria = io.BytesIO()
    documento.save(memoria)
    return memoria.getvalue()


@pytest.fixture()
def contexto():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        tenant = Tenant(name="Girón", code="giron", is_active=True)
        otro = Tenant(name="Otro", code="otro", is_active=True)
        session.add_all([tenant, otro])
        session.commit()
        session.refresh(tenant)
        session.refresh(otro)

        usuario = User(
            email="funcionario@example.com",
            username="funcionario",
            full_name="Funcionario Uno",
            hashed_password="$5$sin_uso",
            role=UserRole.TENANT_ADMIN,
            tenant_id=tenant.id,
            is_active=True,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)

        pagado = WorkflowState(
            code=WorkflowStateCode.PAGADO, name="Pagado", order=90, tenant_id=tenant.id
        )
        inicial = WorkflowState(
            code=WorkflowStateCode.CARTERA_CARGADA, name="Cartera", order=1,
            tenant_id=tenant.id,
        )
        session.add_all([pagado, inicial])
        session.commit()
        session.refresh(pagado)
        session.refresh(inicial)

        cliente = Client(
            tenant_id=tenant.id,
            identification="30208284",
            name="MARLENY BARRERA BARON",
            address="CLL 35 18 57 RINCON DE GIRON",
            email="deudor@example.com",
        )
        cliente_sin_correo = Client(
            tenant_id=tenant.id,
            identification="5529239",
            name="YAEZ PEREZ ALCIDES",
            address="C 68 32 09 LO 18",
        )
        cliente_ajeno = Client(
            tenant_id=otro.id,
            identification="1111111",
            name="OTRO TENANT",
            address="Otros",
            email="otro@example.com",
        )
        session.add_all([cliente, cliente_sin_correo, cliente_ajeno])
        session.commit()
        for item in (cliente, cliente_sin_correo, cliente_ajeno):
            session.refresh(item)

        proceso = CobroProcess(
            tenant_id=tenant.id, reference="PROC-1", current_state_id=pagado.id
        )
        session.add(proceso)
        session.commit()
        session.refresh(proceso)

        # El historial más reciente hacia PAGADO es el que debe derivarse.
        session.add_all([
            ProcessHistory(
                tenant_id=tenant.id, process_id=proceso.id, action="Cambio de estado",
                new_state_id=pagado.id,
                created_at=datetime(2024, 12, 1, 10, 0, 0),
            ),
            ProcessHistory(
                tenant_id=tenant.id, process_id=proceso.id, action="Pago total",
                new_state_id=pagado.id,
                created_at=datetime(2024, 12, 19, 17, 30, 0),
            ),
            ProcessHistory(
                tenant_id=tenant.id, process_id=proceso.id, action="Validación",
                new_state_id=inicial.id,
                created_at=datetime(2025, 1, 15, 8, 0, 0),
            ),
        ])

        obligacion = Obligation(
            client_id=cliente.id,
            process_id=proceso.id,
            amount=156523.0,
            due_date=datetime(2024, 11, 30),
            issue_date=datetime(2024, 1, 1),
            description="000000",
            resolution_number="3849",
            resolution_year=2024,
            resolution_date=date(2024, 11, 13),
        )
        obligacion_constancia = Obligation(
            client_id=cliente_sin_correo.id,
            process_id=proceso.id,
            amount=98000.0,
            due_date=datetime(2025, 4, 30),
            issue_date=datetime(2025, 1, 1),
            description="000001",
            resolution_number="1886",
            resolution_year=2025,
            resolution_date=date(2025, 4, 9),
            executory_date=date(2025, 6, 18),
        )
        obligacion_sin_resolucion = Obligation(
            client_id=cliente.id,
            amount=10.0,
            due_date=datetime(2025, 1, 31),
            issue_date=datetime(2025, 1, 1),
            description="000002",
        )
        obligacion_ajena = Obligation(
            client_id=cliente_ajeno.id,
            amount=20.0,
            due_date=datetime(2025, 1, 31),
            issue_date=datetime(2025, 1, 1),
            description="000003",
            resolution_number="9999",
            resolution_date=date(2025, 1, 10),
        )
        session.add_all([
            obligacion, obligacion_constancia, obligacion_sin_resolucion, obligacion_ajena
        ])
        session.commit()
        for item in (
            obligacion, obligacion_constancia, obligacion_sin_resolucion, obligacion_ajena
        ):
            session.refresh(item)

        plantilla = DocumentTemplate(
            tenant_id=tenant.id,
            name="Auto de Archivo — GD-F.03",
            code="AUTO_ARCHIVO",
            template_type=TemplateType.DOCX,
            is_active=True,
            content=_crear_plantilla_docx(),
        )
        constancia = DocumentTemplate(
            tenant_id=tenant.id,
            name="Constancia Secretarial — GD-F.01",
            code="CONSTANCIA_SECRETARIAL",
            template_type=TemplateType.DOCX,
            is_active=True,
            content=_crear_plantilla_docx(),
        )
        session.add_all([plantilla, constancia])
        session.commit()
        session.refresh(plantilla)
        session.refresh(constancia)

        app = FastAPI()
        app.include_router(documents.router, prefix="/documents")
        app.dependency_overrides[get_session] = lambda: session
        app.dependency_overrides[get_current_active_user] = lambda: usuario

        with TestClient(app) as cliente_api:
            yield {
                "session": session,
                "client": cliente_api,
                "tenant": tenant,
                "otro_tenant": otro,
                "usuario": usuario,
                "obligacion": obligacion,
                "obligacion_constancia": obligacion_constancia,
                "obligacion_sin_resolucion": obligacion_sin_resolucion,
                "obligacion_ajena": obligacion_ajena,
                "proceso": proceso,
                "state_pagado": pagado,
            }


# ─────────────────────────────────────────────────────────────
# Utilidades de fecha
# ─────────────────────────────────────────────────────────────

def test_fecha_larga_es_usa_el_formato_oficial():
    assert documents._fecha_larga_es(date(2025, 4, 9)) == "09 de Abril de 2025"
    assert documents._fecha_larga_es(date(2025, 6, 18)) == "18 de Junio de 2025"
    assert documents._fecha_larga_es(None) == ""


def test_iso_devuelve_formato_del_auto():
    assert documents._iso(date(2025, 3, 4)) == "2025-03-04"
    assert documents._iso(None) == ""


def test_resolver_fecha_pago_prioriza_el_campo_de_la_obligacion(contexto):
    obligation = contexto["obligacion"]
    obligation.paid_date = date(2020, 1, 2)
    contexto["session"].add(obligation)
    contexto["session"].commit()

    assert documents._resolver_fecha_pago(contexto["session"], obligation) == date(2020, 1, 2)


def test_resolver_fecha_pago_toma_el_movimiento_mas_reciente_a_pago(contexto):
    """Debe ser 2024-12-19: hay un movimiento posterior, pero no es de pago."""
    fecha = documents._resolver_fecha_pago(
        contexto["session"], contexto["obligacion"]
    )
    assert fecha == date(2024, 12, 19)


def test_resolver_fecha_pago_devuelve_none_sin_proceso(contexto):
    assert documents._resolver_fecha_pago(
        contexto["session"], contexto["obligacion_sin_resolucion"]
    ) is None


# ─────────────────────────────────────────────────────────────
# Contextos y validaciones
# ─────────────────────────────────────────────────────────────

def test_contexto_auto_archivo_formatos_esperados(contexto):
    obligation = contexto["obligacion"]
    client = contexto["session"].get(Client, obligation.client_id)
    contexto_ = documents._contexto_documento(
        "auto_archivo", obligation, client, {"fecha_pago": date(2024, 12, 19)}
    )
    assert contexto_["numero_resolucion"] == "3849"
    assert contexto_["fecha_resolucion"] == "2024-11-13"
    assert contexto_["fecha_pago"] == "2024-12-19"
    assert contexto_["nombre_usuario"] == "MARLENY BARRERA BARON"
    assert contexto_["direccion_usuario"] == "CLL 35 18 57 RINCON DE GIRON"


def test_contexto_constancia_usa_fechas_en_letras(contexto):
    obligation = contexto["obligacion_constancia"]
    client = contexto["session"].get(Client, obligation.client_id)
    contexto_ = documents._contexto_documento(
        "constancia_secretarial",
        obligation,
        client,
        {
            "fecha_constancia": date(2025, 5, 8),
            "fecha_ejecutoria": date(2025, 6, 18),
        },
    )
    assert contexto_["fecha_constancia"] == "08 de Mayo de 2025"
    assert contexto_["fecha_resolucion_larga"] == "09 de Abril de 2025"
    assert contexto_["fecha_ejecutoria_larga"] == "18 de Junio de 2025"


def test_problemas_documento_bloquea_faltantes():
    obligation = Obligation(
        client_id=1, amount=1.0, due_date=datetime(2025, 1, 1), issue_date=datetime(2025, 1, 1)
    )
    assert documents._problemas_documento("auto_archivo", obligation, {}) == [
        "sin número de resolución",
        "sin fecha de resolución",
        "sin fecha de pago total",
    ]
    obligation.resolution_number = "1"
    obligation.resolution_date = date(2025, 1, 1)
    assert documents._problemas_documento("constancia_secretarial", obligation, {}) == [
        "sin fecha de ejecutoria"
    ]
    assert documents._problemas_documento(
        "constancia_secretarial", obligation, {"fecha_ejecutoria": date(2025, 2, 1)}
    ) == []


# ─────────────────────────────────────────────────────────────
# Previsualización
# ─────────────────────────────────────────────────────────────

def test_preview_resuelve_fechas_derivadas_y_advertencias(contexto):
    response = contexto["client"].post(
        "/documents/auto-archivo/preview",
        json={"obligation_ids": [contexto["obligacion"].id]},
    )

    assert response.status_code == 200
    fila = response.json()[0]
    assert fila["resolution_number"] == "3849"
    assert fila["fechas"]["fecha_pago"] == "2024-12-19"
    assert fila["contexto"]["nombre_usuario"] == "MARLENY BARRERA BARON"
    assert fila["problemas"] == []


def test_preview_advierte_cliente_sin_correo_y_faltantes(contexto):
    response = contexto["client"].post(
        "/documents/auto-archivo/preview",
        json={"obligation_ids": [
            contexto["obligacion_constancia"].id,
            contexto["obligacion_sin_resolucion"].id,
        ]},
    )

    assert response.status_code == 200
    filas = {fila["obligation_id"]: fila for fila in response.json()}
    sin_resolucion = filas[contexto["obligacion_sin_resolucion"].id]
    assert "sin número de resolución" in sin_resolucion["problemas"]
    constancia = filas[contexto["obligacion_constancia"].id]
    assert constancia["email"] == ""
    assert "el cliente no tiene correo registrado" in constancia["advertencias"]


def test_preview_rechaza_obligaciones_de_otro_tenant(contexto):
    response = contexto["client"].post(
        "/documents/auto-archivo/preview",
        json={"obligation_ids": [contexto["obligacion_ajena"].id]},
    )

    assert response.status_code == 400
    assert "no pertenecen al tenant" in response.json()["detail"]


def test_preview_exige_seleccion(contexto):
    assert contexto["client"].post(
        "/documents/constancia/preview", json={"obligation_ids": []}
    ).status_code == 400


# ─────────────────────────────────────────────────────────────
# Generación
# ─────────────────────────────────────────────────────────────

def _lista_zip(payload) -> list:
    with zipfile.ZipFile(io.BytesIO(payload)) as zip_file:
        return zip_file.namelist()


def test_generate_auto_archivo_devuelve_zip_con_docx(contexto):
    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={"obligation_ids": [contexto["obligacion"].id], "formato": "docx"},
    )

    assert response.status_code == 200
    assert response.headers["X-Document-Count"] == "1"
    archivos = _lista_zip(response.content)
    assert len(archivos) == 1
    assert archivos[0].startswith("auto_archivo_3849_30208284")
    assert archivos[0].endswith(".docx")

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        texto = "".join(
            paragraph.text
            for paragraph in Document(io.BytesIO(zip_file.read(archivos[0]))).paragraphs
        )
    assert "3849" in texto
    assert "2024-12-19" in texto
    assert "MARLENY BARRERA BARON" in texto


def test_generate_constancia_aceita_fecha_de_ejecutoria_pendiente(contexto):
    response = contexto["client"].post(
        "/documents/constancia/generate",
        json={"obligation_ids": [contexto["obligacion_constancia"].id], "formato": "docx"},
    )

    assert response.status_code == 200
    assert _lista_zip(response.content)[0].startswith("constancia_secretarial_1886")


def test_generate_bloquea_obligacion_sin_fecha_pago(contexto):
    """Sin resolución ni historial de pago: el auto no se emite."""
    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={"obligation_ids": [contexto["obligacion_sin_resolucion"].id], "formato": "docx"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "sin fecha de pago total" in detail
    assert "sin número de resolución" in detail


def test_generate_con_override_de_fecha_pago(contexto):
    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={
            "obligation_ids": [contexto["obligacion"].id],
            "formato": "docx",
            "fechas": {str(contexto["obligacion"].id): {"fecha_pago": "2025-01-05"}},
        },
    )

    assert response.status_code == 200
    contexto["session"].refresh(contexto["obligacion"])
    # Sin persistir_fechas la corrección es solo para este documento.
    assert contexto["obligacion"].paid_date is None


def test_generate_persiste_las_fechas_editadas(contexto):
    obligation = contexto["obligacion"]
    constancia = contexto["obligacion_constancia"]
    responses = [
        contexto["client"].post(
            "/documents/auto-archivo/generate",
            json={
                "obligation_ids": [obligation.id],
                "formato": "docx",
                "fechas": {str(obligation.id): {"fecha_pago": "2025-02-03"}},
                "persistir_fechas": True,
            },
        ),
        contexto["client"].post(
            "/documents/constancia/generate",
            json={
                "obligation_ids": [constancia.id],
                "formato": "docx",
                "fechas": {
                    str(constancia.id): {
                        "fecha_notificacion": "2025-05-02",
                        "fecha_ejecutoria": "2025-06-18",
                    }
                },
                "persistir_fechas": True,
            },
        ),
    ]
    assert [respuesta.status_code for respuesta in responses] == [200, 200]

    contexto["session"].refresh(obligation)
    contexto["session"].refresh(constancia)
    assert obligation.paid_date == date(2025, 2, 3)
    assert constancia.notification_date == date(2025, 5, 2)
    assert constancia.executory_date == date(2025, 6, 18)


def test_generate_ambos_convierte_pdf_y_registra_documentos(contexto, monkeypatch):
    def _falso_pdf(docx_path, pdf_path, perfil_dir):
        with open(pdf_path, "wb") as archivo:
            archivo.write(b"%PDF-1.4 prueba")

    monkeypatch.setattr(documents, "_convertir_docx_a_pdf", _falso_pdf)

    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={
            "obligation_ids": [contexto["obligacion"].id],
            "formato": "ambos",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-File-Count"] == "2"
    nombres = _lista_zip(response.content)
    assert len(nombres) == 2
    assert {nombre.rsplit(".", 1)[-1] for nombre in nombres} == {"docx", "pdf"}

    registros = contexto["session"].exec(
        select(GeneratedDocument).where(GeneratedDocument.tenant_id == contexto["tenant"].id)
    ).all()
    assert {registro.document_type for registro in registros} == {"DOCX", "PDF"}
    assert {registro.resolution_number for registro in registros} == {"3849"}


def test_generate_pdf_sin_libreoffice_falla_claro(contexto, monkeypatch):
    """Se fuerza el error de conversión para validar el mensaje, sin LibreOffice."""
    def _explode(docx_path, pdf_path, perfil_dir):
        raise documents.HTTPException(status_code=500, detail="libreoffice no disponible")

    monkeypatch.setattr(documents, "_convertir_docx_a_pdf", _explode)

    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={"obligation_ids": [contexto["obligacion"].id], "formato": "pdf"},
    )

    assert response.status_code == 500
    assert "libreoffice no disponible" in response.json()["detail"]


def test_generate_rechaza_formato_invalido(contexto):
    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={"obligation_ids": [contexto["obligacion"].id], "formato": "xlsx"},
    )

    assert response.status_code == 400
    assert "docx, pdf o ambos" in response.json()["detail"]


def test_generate_sin_plantilla_registrada_devuelve_404(contexto):
    plantilla = contexto["session"].exec(
        select(DocumentTemplate).where(DocumentTemplate.code == "AUTO_ARCHIVO")
    ).first()
    plantilla.is_active = False
    contexto["session"].add(plantilla)
    contexto["session"].commit()

    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={"obligation_ids": [contexto["obligacion"].id], "formato": "docx"},
    )

    assert response.status_code == 404
    assert "AUTO_ARCHIVO" in response.json()["detail"]


# ─────────────────────────────────────────────────────────────
# Correo
# ─────────────────────────────────────────────────────────────

def test_generate_envia_correo_reportado_en_cabeceras(contexto, monkeypatch):
    enviados = []

    def _falso_envio(to_email, subject, html_content, attachments, smtp_config):
        enviados.append({
            "to_email": to_email,
            "subject": subject,
            "adjuntos": [adjunto["filename"] for adjunto in attachments],
        })
        return True

    monkeypatch.setattr(EmailService, "send_document_email", staticmethod(_falso_envio))
    monkeypatch.setattr(
        documents, "_config_smtp", lambda: {"smtp_host": "smtp", "smtp_port": 587}
    )

    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={
            "obligation_ids": [
                contexto["obligacion"].id,
                contexto["obligacion_constancia"].id,
            ],
            "formato": "docx",
            "enviar_correo": True,
            "destinatarios": {str(contexto["obligacion_constancia"].id): "manual@example.com"},
            "fechas": {str(contexto["obligacion_constancia"].id): {"fecha_pago": "2025-01-01"}},
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Email-Sent"] == "2"
    assert response.headers["X-Email-Failed"] == "0"
    # Una usa el correo del cliente; la otra el destinatario digitado en el diálogo.
    assert sorted(item["to_email"] for item in enviados) == [
        "deudor@example.com", "manual@example.com"
    ]
    assert all(len(item["adjuntos"]) == 1 for item in enviados)


def test_generate_cuenta_como_fallido_un_envio_error(contexto, monkeypatch):
    monkeypatch.setattr(
        EmailService, "send_document_email", staticmethod(lambda **kwargs: False)
    )
    monkeypatch.setattr(
        documents, "_config_smtp", lambda: {"smtp_host": "smtp", "smtp_port": 587}
    )

    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={
            "obligation_ids": [contexto["obligacion"].id],
            "formato": "docx",
            "enviar_correo": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Email-Sent"] == "0"
    assert response.headers["X-Email-Failed"] == "1"


def test_generate_sin_smtp_configurado_no_envia(contexto, monkeypatch):
    monkeypatch.setattr(documents, "_config_smtp", lambda: None)

    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={
            "obligation_ids": [contexto["obligacion"].id],
            "formato": "docx",
            "enviar_correo": True,
        },
    )

    assert response.status_code == 400
    assert "correo no está configurado" in response.json()["detail"]


def test_email_service_monta_adjuntos_y_no_rompe_las_invitaciones(monkeypatch):
    enviados = {}

    class ServidorFalso:
        def __init__(self, host, port):
            pass

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def sendmail(self, from_email, to_email, mensaje):
            enviados["mensaje"] = mensaje

        def quit(self):
            pass

    monkeypatch.setattr(smtplib, "SMTP", ServidorFalso)

    ok = EmailService.send_email(
        to_email="deudor@example.com",
        subject="Auto de Archivo",
        html_content="<p>Cordial saludo</p>",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="remite@example.com",
        smtp_password="secreto",
        attachments=[
            {"filename": "auto.docx", "content": b"xyz"},
            {"filename": "auto.pdf", "content": b"%PDF"},
        ],
    )

    assert ok is True
    mensaje = enviados["mensaje"]
    assert "multipart/mixed" in mensaje
    assert 'filename="auto.docx"' in mensaje
    assert 'filename="auto.pdf"' in mensaje

    # Retrocompatibilidad: sin adjuntos sigue siendo un correo de cuerpo único.
    enviados.clear()
    assert EmailService.send_email(
        to_email="nuevo@example.com",
        subject="Invitación",
        html_content="<p>Bienvenido</p>",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="remite@example.com",
        smtp_password="secreto",
    )
    assert "multipart/mixed" not in enviados["mensaje"]
    assert "Bienvenido" in enviados["mensaje"]


def test_email_service_reporta_fallo_sin_explotar(monkeypatch):
    class ServidorRechazado:
        def __init__(self, host, port):
            raise OSError("conexión rechazada")

    monkeypatch.setattr(smtplib, "SMTP", ServidorRechazado)

    assert EmailService.send_email(
        to_email="deudor@example.com",
        subject="Auto de Archivo",
        html_content="<p>x</p>",
        smtp_host="smtp",
        smtp_port=25,
        smtp_user="u",
        smtp_password="p",
    ) is False


# ─────────────────────────────────────────────────────────────
# Plantillas oficiales convertidas
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre", [
    "1_auto_de_archivo.docx",
    "1_constancia_secretarial.docx",
])
def test_plantillas_oficiales_renderizan_sin_tags_colgados(nombre):
    """Render real de la plantilla convertida: ningún {{ }} debe quedar visible."""
    import os

    ruta = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "uploads", "templates", nombre,
    )
    if not os.path.exists(ruta):
        pytest.skip("la plantilla convertida no está en el árbol de trabajo")

    from docxtpl import DocxTemplate

    datos = {
        "numero_resolucion": "3849",
        "fecha_resolucion": "2024-11-13",
        "fecha_pago": "2024-12-19",
        "fecha_constancia": "08 de Mayo de 2025",
        "fecha_resolucion_larga": "09 de Abril de 2025",
        "fecha_ejecutoria_larga": "18 de Junio de 2025",
        "nombre_usuario": "PRUEBA SIN DATOS REALES",
        "documento_usuario": "1010101",
        "direccion_usuario": "CL 1 1 1",
        "cuenta_usuario": "000000",
    }
    documento = DocxTemplate(ruta)
    documento.render(datos)
    texto = "\n".join(p.text for p in documento.docx.paragraphs)

    assert "{{" not in texto
    assert "}}" not in texto
    assert "3849" in texto
