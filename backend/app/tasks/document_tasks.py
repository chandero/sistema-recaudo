"""Tareas Celery para generación masiva de documentos."""
import os
import zipfile
from datetime import datetime
from sqlmodel import Session, select

from app.celery_app import celery_app
from app.core.database import engine
from app.models.document import DocumentTemplate, GeneratedDocument
from app.models.process import CobroProcess
from app.models.client import Client
from app.models.obligation import Obligation
from app.services.document_generation_service import DocumentGenerationService

OUTPUT_DIR = "app/uploads/generated"


@celery_app.task(name="app.tasks.document_tasks.generate_mass_documents")
def generate_mass_documents(template_id: int, process_ids: list, tenant_id: int, user_id: int):
    """Genera documentos masivamente para múltiples procesos y los empaqueta en ZIP.

    Returns:
        dict con la ruta del ZIP generado y el número de documentos creados.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    batch_dir = os.path.join(OUTPUT_DIR, f"mass_{tenant_id}_{stamp}")
    os.makedirs(batch_dir, exist_ok=True)

    generated = 0
    errors = 0

    with Session(engine) as session:
        template = session.get(DocumentTemplate, template_id)
        if not template or template.tenant_id != tenant_id:
            return {"error": "Plantilla no encontrada", "generated": 0}

        # Guardar plantilla temporal
        template_path = os.path.join(batch_dir, "template.docx")
        with open(template_path, "wb") as f:
            f.write(template.content)

        zip_path = os.path.join(OUTPUT_DIR, f"documentos_masivos_{stamp}.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for pid in process_ids:
                try:
                    process = session.get(CobroProcess, pid)
                    if not process or process.tenant_id != tenant_id:
                        errors += 1
                        continue

                    # Obtener cliente y obligaciones
                    obligations = session.exec(
                        select(Obligation).where(Obligation.process_id == pid)
                    ).all()

                    client = None
                    for obl in obligations:
                        c = session.get(Client, obl.client_id)
                        if c:
                            client = c
                            break

                    variables = {
                        "referencia": process.reference,
                        "cliente_nombre": client.name if client else "N/A",
                        "cliente_identificacion": client.identification if client else "N/A",
                        "cliente_direccion": client.address if client else "",
                        "cliente_telefono": client.phone if client else "",
                        "cliente_email": client.email if client else "",
                        "total_obligaciones": len(obligations),
                        "valor_total": sum(o.amount for o in obligations),
                        "fecha_generacion": datetime.utcnow().strftime("%d/%m/%Y"),
                    }

                    filename = f"doc_{process.reference}_{stamp}.docx"
                    output_path = os.path.join(batch_dir, filename)
                    DocumentGenerationService.render_template(template_path, variables, output_path)
                    zf.write(output_path, filename)

                    # Registrar documento generado
                    doc = GeneratedDocument(
                        tenant_id=tenant_id,
                        process_id=pid,
                        template_id=template_id,
                        client_id=client.id if client else None,
                        file_path=output_path,
                        filename=filename,
                        document_type="DOCX",
                        file_size=os.path.getsize(output_path),
                        created_by=user_id,
                    )
                    session.add(doc)
                    generated += 1

                except Exception:
                    errors += 1
                    continue

            session.commit()

    return {
        "zip_path": zip_path,
        "generated": generated,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat(),
    }
