#!/usr/bin/env python3
"""
Registra (o actualiza) las plantillas de Auto de Archivo y Constancia Secretarial
en la tabla document_templates, una fila por tenant.

Es idempotente: si el DOCX no cambió, la fila queda intacta; si cambió, se
actualiza el binario y se incrementa la versión. No duplica códigos.

Uso (dentro del contenedor del backend, o desde backend/ con el venv activo):
    python scripts/registrar_plantillas.py                # todos los tenants
    python scripts/registrar_plantillas.py --tenant-id 1  # un tenant
    python scripts/registrar_plantillas.py --dry-run      # solo informa
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.models.document import DocumentTemplate, TemplateType  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402

# Mismo destino que UPLOAD_DIR en app/api/v1/endpoints/documents.py.
PLANTILLA_DIR = os.path.join("app", "uploads", "templates")

# Campos que el formulario del frontend debe ofrecer por tipo de documento.
_ETIQUETAS = {
    "numero_resolucion": "Número de resolución",
    "fecha_resolucion": "Fecha de resolución (AAAA-MM-DD)",
    "fecha_resolucion_larga": "Fecha de resolución en letras",
    "fecha_constancia": "Fecha de la constancia en letras",
    "fecha_pago": "Fecha de pago total (AAAA-MM-DD)",
    "fecha_ejecutoria_larga": "Fecha de ejecutoria en letras",
    "nombre_usuario": "Nombre del contribuyente",
    "documento_usuario": "Identificación del contribuyente",
    "direccion_usuario": "Dirección del contribuyente",
    "cuenta_usuario": "Cuenta / referencia de la obligación",
}

PLANES = [
    {
        "archivo": "1_auto_de_archivo.docx",
        "code": "AUTO_ARCHIVO",
        "name": "Auto de Archivo — GD-F.03",
        "description": (
            "Auto de archivo y terminación por pago total de la deuda "
            "(formato oficial GD-F.03)."
        ),
    },
    {
        "archivo": "1_constancia_secretarial.docx",
        "code": "CONSTANCIA_SECRETARIAL",
        "name": "Constancia Secretarial — GD-F.01",
        "description": (
            "Constancia secretarial de acto administrativo en firme "
            "(formato oficial GD-F.01)."
        ),
    },
]

_TAG = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def _variables(docx_path: str) -> dict:
    """Extrae los placeholders reales del DOCX para el variables_schema."""
    texto = ""
    with zipfile.ZipFile(docx_path) as archivo:
        for nombre in archivo.namelist():
            if re.match(r"word/(document|header\d*|footer\d*)\.xml$", nombre):
                # Se quitan las etiquetas XML antes de buscar: Word suele partir
                # '{{campo}}' en varios runs y el placeholder solo se ve al
                # concatenar el texto de los runs contiguos.
                texto += re.sub(r"<[^>]+>", "", archivo.read(nombre).decode("utf-8", "ignore"))
    encontrados = []
    for valor in _TAG.findall(texto):
        if valor not in encontrados:
            encontrados.append(valor)
    validos = [v for v in encontrados if v in _ETIQUETAS]
    descartados = [v for v in encontrados if v not in _ETIQUETAS]
    if descartados:
        print(f"[ADVERTENCIA] {os.path.basename(docx_path)} tiene variables desconocidas: {descartados}")
    return {
        "variables": validos,
        "etiquetas": {v: _ETIQUETAS[v] for v in validos},
        "fuente": os.path.basename(docx_path),
    }


def _registros(session: Session, tenant_id: int) -> int:
    """Crea o actualiza las plantillas de un tenant. Devuelve filas tocadas."""
    tocadas = 0
    for plan in PLANES:
        ruta = os.path.join(PLANTILLA_DIR, plan["archivo"])
        if not os.path.exists(ruta):
            print(f"[ADVERTENCIA] falta el archivo {ruta}; se omite {plan['code']}")
            continue
        with open(ruta, "rb") as archivo:
            contenido = archivo.read()
        schema = _variables(ruta)

        existente = session.exec(
            select(DocumentTemplate).where(
                DocumentTemplate.tenant_id == tenant_id,
                DocumentTemplate.code == plan["code"],
            )
        ).first()

        if existente and existente.content == contenido:
            print(f"[IGUAL] tenant {tenant_id}: {plan['code']} v{existente.version}")
            continue

        if existente:
            existente.name = plan["name"]
            existente.description = plan["description"]
            existente.template_type = TemplateType.DOCX
            existente.is_active = True
            existente.version = (existente.version or 1) + 1
            existente.content = contenido
            existente.variables_schema = schema
            existente.updated_at = datetime.utcnow()
            print(f"[ACTUALIZA] tenant {tenant_id}: {plan['code']} v{existente.version}")
        else:
            session.add(DocumentTemplate(
                tenant_id=tenant_id,
                name=plan["name"],
                code=plan["code"],
                description=plan["description"],
                template_type=TemplateType.DOCX,
                version=1,
                is_active=True,
                content=contenido,
                variables_schema=schema,
            ))
            print(f"[CREA] tenant {tenant_id}: {plan['code']} v1")
        tocadas += 1
    return tocadas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", type=int, help="Limitar el registro a un tenant")
    parser.add_argument("--dry-run", action="store_true", help="No escribe en la base de datos")
    args = parser.parse_args()

    if not os.path.isdir(PLANTILLA_DIR):
        print(f"[ERROR] no existe {PLANTILLA_DIR}; ejecute primero scripts/convierte_plantillas.py")
        return 1

    with Session(engine) as session:
        if args.tenant_id:
            tenants = session.exec(select(Tenant).where(Tenant.id == args.tenant_id)).all()
            if not tenants:
                print(f"[ERROR] el tenant {args.tenant_id} no existe")
                return 1
        else:
            tenants = session.exec(select(Tenant)).all()

        print(f"Tenant(s) a procesar: {[t.id for t in tenants]}")
        total = 0
        for tenant in tenants:
            total += _registros(session, tenant.id)
        if args.dry_run:
            session.rollback()
            print("[DRY RUN] no se guardaron cambios")
        else:
            session.commit()
            print(f"Listo: {total} fila(s) creadas o actualizadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
