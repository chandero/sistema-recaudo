"""
Pruebas de generación del Auto de Archivo (GD-F.03) y la Constancia Secretarial
(GD-F.01): contextos, derivación de fechas, endpoints de preview/generate,
aislamiento por tenant y envío de correo con adjuntos.
"""
import io
import os
import re
import smtplib
import tempfile
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
from app.services.template_utils import (
    VARIABLES_OBLIGATORIAS,
    extraer_placeholders,
    validar_plantilla,
)


def _crear_plantilla_docx(marca: str = "") -> bytes:
    """Plantilla mínima con todos los placeholders de los dos documentos."""
    documento = Document()
    if marca:
        documento.add_paragraph(marca)
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
    # El formato vigente de la constancia no imprime la fecha de ejecutoria.
    assert documents._problemas_documento("constancia_secretarial", obligation, {}) == []
    assert documents._problemas_documento("auto_archivo", obligation, {}) == [
        "sin fecha de pago total"
    ]


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


def test_generate_sin_smtp_configurado_entrega_el_zip(contexto, monkeypatch):
    """Sin SMTP el correo es opcional: no se aborta la generación del documento."""
    monkeypatch.setattr(documents, "_config_smtp", lambda: None)

    response = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={
            "obligation_ids": [contexto["obligacion"].id],
            "formato": "docx",
            "enviar_correo": True,
        },
    )

    assert response.status_code == 200
    archivos = _lista_zip(response.content)
    assert len(archivos) == 1
    assert archivos[0].startswith("auto_archivo_")
    assert archivos[0].endswith(".docx")
    assert response.headers["X-Email-Sent"] == "0"
    assert response.headers["X-Email-Failed"] == "1"
    assert response.headers["X-Email-Note"] == "smtp_no_configurado"


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

def _ruta_plantilla(nombre: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "uploads", "templates", nombre,
    )


def test_constancia_oficial_tiene_las_variables_del_formato_vigente():
    """Fija el formato nuevo: sin ejecutoria y sin datos del deudor."""
    ruta = _ruta_plantilla("1_constancia_secretarial.docx")
    if not os.path.exists(ruta):
        pytest.skip("la plantilla convertida no está en el árbol de trabajo")

    with open(ruta, "rb") as archivo:
        contenido = archivo.read()
    variables = extraer_placeholders(contenido)

    assert set(variables) == set(VARIABLES_OBLIGATORIAS["CONSTANCIA_SECRETARIAL"])
    assert "fecha_ejecutoria_larga" not in variables
    # Validación equivalente a la del endpoint de reemplazo.
    assert validar_plantilla(contenido, "CONSTANCIA_SECRETARIAL") == variables


def test_auto_oficial_variables_la_resolucion_del_caso_en_todo_el_cuerpo():
    """El cuerpo del Auto de Archivo no puede conservar el número del ejemplo."""
    ruta = _ruta_plantilla("1_auto_de_archivo.docx")
    if not os.path.exists(ruta):
        pytest.skip("la plantilla convertida no está en el árbol de trabajo")

    with open(ruta, "rb") as archivo:
        contenido = archivo.read()
    variables = extraer_placeholders(contenido)
    assert set(variables) == set(VARIABLES_OBLIGATORIAS["AUTO_ARCHIVO"])
    assert validar_plantilla(contenido, "AUTO_ARCHIVO") == variables

    with zipfile.ZipFile(ruta) as paquete:
        texto = re.sub(
            r"<[^>]+>", "", paquete.read("word/document.xml").decode("utf-8")
        )
    # Se cita la resolución del caso en el encabezado y dos veces en el cuerpo.
    assert texto.count("{{numero_resolucion}}") == 3
    assert texto.count("{{fecha_resolucion}}") == 3


def test_plantillas_oficiales_no_conservan_autor_en_metadatos():
    """docProps/core.xml no puede traer el nombre ni el correo del funcionario."""
    for nombre in ("1_auto_de_archivo.docx", "1_constancia_secretarial.docx"):
        ruta = _ruta_plantilla(nombre)
        if not os.path.exists(ruta):
            pytest.skip("la plantilla convertida no está en el árbol de trabajo")
        with zipfile.ZipFile(ruta) as paquete:
            core = paquete.read("docProps/core.xml").decode("utf-8", "ignore")
        cuerpo = re.findall(r"<(?:dc:creator|cp:lastModifiedBy)[^>]*>(.*?)</", core, re.S)
        assert all(not valor.strip() for valor in cuerpo), f"{nombre} conserva {cuerpo}"


@pytest.mark.parametrize("nombre", [
    "1_auto_de_archivo.docx",
    "1_constancia_secretarial.docx",
])
def test_plantillas_oficiales_renderizan_sin_tags_colgados(nombre):
    """Render real de la plantilla convertida: ningún {{ }} debe quedar visible."""
    ruta = _ruta_plantilla(nombre)
    if not os.path.exists(ruta):
        pytest.skip("la plantilla convertida no está en el árbol de trabajo")

    from docxtpl import DocxTemplate

    # Valores deliberadamente distintos a los del formato diligenciado que se
    # convirtió, para que una fuga de datos del ejemplo se detecte aquí.
    datos = {
        "numero_resolucion": "7777",
        "fecha_resolucion": "2030-01-31",
        "fecha_pago": "2030-02-27",
        "fecha_constancia": "31 de Enero de 2030",
        "fecha_resolucion_larga": "31 de Enero de 2030",
        "fecha_ejecutoria_larga": "18 de Febrero de 2030",
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
    assert "7777" in texto
    for fugado in ("3849", "2024-11-13", "0447", "2025-03-04", "MARLENY",
                   "30208284", "MARQUEZ", "28150302", "10879"):
        assert fugado not in texto, f"{nombre} imprime el dato del ejemplo {fugado}"
    # Toda variable del contexto llega al documento renderizado.
    assert "PRUEBA SIN DATOS REALES" in texto
    assert "1010101" in texto
    assert "CL 1 1 1" in texto


# ─────────────────────────────────────────────────────────────
# Reemplazo del DOCX de una plantilla registrada
# ─────────────────────────────────────────────────────────────

def _subir_plantilla(cliente_api, code: str, contenido: bytes, nombre: str = "nueva.docx"):
    return cliente_api.put(
        f"/documents/templates/{code}/content",
        files={
            "file": (
                nombre,
                io.BytesIO(contenido),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )


def _docx_plano(texto: str) -> bytes:
    documento = Document()
    documento.add_paragraph(texto)
    memoria = io.BytesIO()
    documento.save(memoria)
    return memoria.getvalue()


def test_reemplazo_actualiza_binario_version_y_espejo(contexto, tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    session = contexto["session"]
    plantilla = session.exec(
        select(DocumentTemplate).where(DocumentTemplate.code == "AUTO_ARCHIVO")
    ).first()
    version_anterior = plantilla.version
    nuevo = _crear_plantilla_docx(marca="FORMATO 2026")

    respuesta = _subir_plantilla(contexto["client"], "AUTO_ARCHIVO", nuevo)

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["version"] == version_anterior + 1
    assert respuesta.headers["X-Template-Version"] == str(version_anterior + 1)
    session.refresh(plantilla)
    assert plantilla.content == nuevo
    assert "fecha_pago" in plantilla.variables_schema["variables"]
    assert plantilla.variables_schema["desconocidas"] == []
    assert (tmp_path / "1_auto_de_archivo.docx").read_bytes() == nuevo


def test_reemplazo_rechaza_un_docx_sin_variables(contexto, tmp_path, monkeypatch):
    """Un formato con datos impresos no puede registrarse: imprimiría igual para todos."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))

    respuesta = _subir_plantilla(
        contexto["client"], "AUTO_ARCHIVO", _docx_plano("Resolución N. 3849 de MARLENY BARRERA")
    )

    assert respuesta.status_code == 400
    assert "no contiene variables" in respuesta.json()["detail"]
    assert not (tmp_path / "1_auto_de_archivo.docx").exists()


def test_reemplazo_rechaza_variables_requeridas_faltantes(contexto, tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))

    respuesta = _subir_plantilla(
        contexto["client"], "AUTO_ARCHIVO", _docx_plano("Solo {{nombre_usuario}} y {{fecha_pago}}")
    )

    assert respuesta.status_code == 400
    detail = respuesta.json()["detail"]
    assert "faltan variables requeridas" in detail
    assert "numero_resolucion" in detail
    assert "fecha_pago" not in detail.split(":", 1)[1]


def test_reemplazo_rechaza_extension_no_permitida(contexto):
    respuesta = contexto["client"].put(
        "/documents/templates/AUTO_ARCHIVO/content",
        files={"file": ("formato.txt", io.BytesIO(b"texto plano"), "text/plain")},
    )

    assert respuesta.status_code == 400
    assert "Tipo de archivo no permitido" in respuesta.json()["detail"]


def test_reemplazo_exige_codigo_existente_del_tenant(contexto):
    respuesta = _subir_plantilla(
        contexto["client"], "SIN_REGISTRO", _crear_plantilla_docx()
    )

    assert respuesta.status_code == 404
    assert "SIN_REGISTRO" in respuesta.json()["detail"]


def test_reemplazo_no_toca_la_plantilla_de_otro_tenant(contexto, tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    session = contexto["session"]
    ajena = DocumentTemplate(
        tenant_id=contexto["otro_tenant"].id,
        code="AUTO_ARCHIVO",
        name="Auto de Archivo ajeno",
        template_type=TemplateType.DOCX,
        is_active=True,
        content=_crear_plantilla_docx(marca="ORIGINAL AJENO"),
    )
    session.add(ajena)
    session.commit()
    session.refresh(ajena)
    contenido_ajeno = ajena.content

    respuesta = _subir_plantilla(
        contexto["client"], "AUTO_ARCHIVO", _crear_plantilla_docx(marca="NUEVO PROPIO")
    )

    assert respuesta.status_code == 200
    session.refresh(ajena)
    assert ajena.content == contenido_ajeno
    assert ajena.version == 1


def test_la_generacion_usa_el_binario_reemplazado(contexto, tmp_path, monkeypatch):
    """La generación lee el BLOB de la base de datos, no el archivo en disco."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    assert _subir_plantilla(
        contexto["client"], "AUTO_ARCHIVO", _crear_plantilla_docx(marca="FORMATO-NUEVO-2026")
    ).status_code == 200

    respuesta = contexto["client"].post(
        "/documents/auto-archivo/generate",
        json={"obligation_ids": [contexto["obligacion"].id], "formato": "docx"},
    )

    assert respuesta.status_code == 200, respuesta.text
    archivos = _lista_zip(respuesta.content)
    with zipfile.ZipFile(io.BytesIO(respuesta.content)) as zip_file:
        texto = "".join(
            paragraph.text
            for paragraph in Document(io.BytesIO(zip_file.read(archivos[0]))).paragraphs
        )
    assert "FORMATO-NUEVO-2026" in texto
    assert "3849" in texto


# ─────────────────────────────────────────────────────────────────
# Vista previa genérica de DocumentosView: /templates/{id}/generate
# ─────────────────────────────────────────────────────────────────

def _texto_docx(payload: bytes) -> str:
    """Texto de un DOCX suelto: este endpoint no responde con ZIP como los lotes."""
    return "\n".join(p.text for p in Document(io.BytesIO(payload)).paragraphs)


def _plantilla(contexto, codigo: str) -> DocumentTemplate:
    return contexto["session"].exec(
        select(DocumentTemplate).where(DocumentTemplate.code == codigo)
    ).first()


def test_vista_previa_usa_el_binario_poniendo_el_espejo_con_otro_nombre(contexto, tmp_path, monkeypatch):
    """El espejo en disco se llama por nombre legible, no por el código."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    # Reproducen el estado del servidor: existe 1_constancia_secretarial.docx y la
    # búsqueda por código (1_CONSTANCIA_SECRETARIAL.docx) no encuentra nada.
    (tmp_path / "1_constancia_secretarial.docx").write_bytes(
        _crear_plantilla_docx(marca="ESPEJO-ANTIGUO")
    )
    plantilla = _plantilla(contexto, "CONSTANCIA_SECRETARIAL")
    obligacion = contexto["obligacion_constancia"]

    respuesta = contexto["client"].post(
        f"/documents/templates/{plantilla.id}/generate",
        json={"obligation_id": obligacion.id},
    )

    assert respuesta.status_code == 200, respuesta.text
    texto = _texto_docx(respuesta.content)
    assert "ESPEJO-ANTIGUO" not in texto
    assert obligacion.resolution_number in texto


def test_vista_previa_sin_binario_sigue_resolviendo_el_disco(contexto, tmp_path, monkeypatch):
    """Las plantillas anteriores al BLOB se generan desde el archivo en disco."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    legacy = DocumentTemplate(
        tenant_id=contexto["tenant"].id,
        code="GD-F.03",
        name="Acto administrativo legado",
        template_type=TemplateType.DOCX,
        is_active=True,
        content=b"",
    )
    contexto["session"].add(legacy)
    contexto["session"].commit()
    contexto["session"].refresh(legacy)
    (tmp_path / "1_GD-F.03Acto_administrativo.docx").write_bytes(
        _crear_plantilla_docx(marca="ESPEJO-LEGADO")
    )

    respuesta = contexto["client"].post(
        f"/documents/templates/{legacy.id}/generate",
        json={"numero_resolucion": "5151"},
    )

    assert respuesta.status_code == 200, respuesta.text
    assert "ESPEJO-LEGADO" in _texto_docx(respuesta.content)


def test_vista_previa_sin_binario_y_sin_archivo_avisa_claramente(contexto, tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    hueca = DocumentTemplate(
        tenant_id=contexto["tenant"].id,
        code="SIN_ARCHIVO",
        name="Plantilla sin soporte",
        template_type=TemplateType.DOCX,
        is_active=True,
        content=b"",
    )
    contexto["session"].add(hueca)
    contexto["session"].commit()
    contexto["session"].refresh(hueca)

    respuesta = contexto["client"].post(
        f"/documents/templates/{hueca.id}/generate", json={}
    )

    assert respuesta.status_code == 500
    assert "Archivo de plantilla no encontrado" in respuesta.json()["detail"]


def test_vista_previa_no_deja_copias_temporales_de_la_plantilla(contexto, tmp_path, monkeypatch):
    """La copia del BLOB se consume al renderizar y se borra siempre."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    creados = []
    original = tempfile.NamedTemporaryFile

    def registrar(*args, **kwargs):
        archivo = original(*args, **kwargs)
        creados.append(archivo.name)
        return archivo

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", registrar)
    plantilla = _plantilla(contexto, "AUTO_ARCHIVO")

    respuesta = contexto["client"].post(
        f"/documents/templates/{plantilla.id}/generate",
        json={"obligation_id": contexto["obligacion"].id},
    )

    assert respuesta.status_code == 200, respuesta.text
    assert creados
    assert [nombre for nombre in creados if os.path.exists(nombre)] == []


def test_vista_previa_de_formato_oficial_sin_obligacion_se_rechaza(contexto, tmp_path, monkeypatch):
    """No se emite un documento oficial con datos de ejemplo."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    plantilla = _plantilla(contexto, "AUTO_ARCHIVO")

    respuesta = contexto["client"].post(
        f"/documents/templates/{plantilla.id}/generate",
        json={"nombre_usuario": "Cliente Prueba"},
    )

    assert respuesta.status_code == 400
    assert "obligación real" in respuesta.json()["detail"]


def test_vista_previa_ignora_el_cuerpo_y_usa_lo_almacenado(contexto, tmp_path, monkeypatch):
    """Si llegan variables en la petición, gana lo que hay en la base de datos."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    plantilla = _plantilla(contexto, "CONSTANCIA_SECRETARIAL")
    obligacion = contexto["obligacion_constancia"]

    respuesta = contexto["client"].post(
        f"/documents/templates/{plantilla.id}/generate",
        json={
            "obligation_id": obligacion.id,
            "numero_resolucion": "VALOR-FICTICIO",
            "nombre_usuario": "Cliente Prueba",
        },
    )

    assert respuesta.status_code == 200, respuesta.text
    texto = _texto_docx(respuesta.content)
    assert obligacion.resolution_number in texto
    assert "VALOR-FICTICIO" not in texto
    assert "Cliente Prueba" not in texto


def test_vista_previa_de_obligacion_incompleta_informa_el_faltante(contexto, tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    plantilla = _plantilla(contexto, "AUTO_ARCHIVO")

    respuesta = contexto["client"].post(
        f"/documents/templates/{plantilla.id}/generate",
        json={"obligation_id": contexto["obligacion_sin_resolucion"].id},
    )

    assert respuesta.status_code == 400
    assert "no se puede previsualizar" in respuesta.json()["detail"]


def test_vista_previa_de_plantilla_de_caso_usa_el_cliente_real_de_la_obligacion(contexto, tmp_path, monkeypatch):
    """Los datos del deudor salen del cliente vinculado, nunca de un literal."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path))
    plantilla = _plantilla(contexto, "AUTO_ARCHIVO")
    session = contexto["session"]
    obligacion = contexto["obligacion"]
    client = session.exec(select(Client).where(Client.id == obligacion.client_id)).first()

    respuesta = contexto["client"].post(
        f"/documents/templates/{plantilla.id}/generate",
        json={"obligation_id": obligacion.id},
    )

    assert respuesta.status_code == 200, respuesta.text
    texto = _texto_docx(respuesta.content)
    assert client.name in texto
    assert client.identification in texto
