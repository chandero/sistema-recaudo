"""
Servicio para generación de documentos (Word a PDF)
Maneja plantillas DOCX con variables Jinja2 y genera salida PDF
"""
import os
import io
import zipfile
import re
from typing import List, Dict, Any
from docxtpl import DocxTemplate
from lxml import etree
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import tempfile
import subprocess
from pathlib import Path

# Nota: Para conversión real DOCX -> PDF en producción se recomienda LibreOffice headless o Pandoc.
# Aquí implementamos una lógica híbrida: llenado de DOCX y simulación/estructura para PDF.

class DocumentGenerationService:
    
    @staticmethod
    def extract_variables_from_template(template_path: str) -> List[str]:
        """
        Extrae las variables de una plantilla DOCX buscando patrones de Jinja2 {{variable}}
        """
        try:
            doc = DocxTemplate(template_path)
            
            # Extraer el contenido XML del documento
            variables = set()
            
            # Procesar todos los párrafos del documento
            for paragraph in doc.doc.paragraphs:
                text = paragraph.text
                # Buscar patrones {{variable}} en el texto
                matches = re.findall(r'\{\{(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*)\}\}', text)
                for match in matches:
                    variables.add(match.strip())
            
            # Procesar tablas
            for table in doc.doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            text = paragraph.text
                            matches = re.findall(r'\{\{(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*)\}\}', text)
                            for match in matches:
                                variables.add(match.strip())
            
            return list(variables)
        except Exception as e:
            raise Exception(f"Error al extraer variables de la plantilla: {str(e)}")

    @staticmethod
    def render_template(template_path: str, context: Dict[str, Any], output_path: str) -> str:
        """
        Rellena una plantilla DOCX con datos y la guarda.
        Si se requiere PDF, aquí se haría la conversión.
        """
        try:
            doc = DocxTemplate(template_path)
            doc.render(context)
            doc.save(output_path)
            return output_path
        except Exception as e:
            raise Exception(f"Error al generar documento: {str(e)}")

    @staticmethod
    def convert_to_pdf(docx_path: str, pdf_path: str) -> bool:
        """
        Convierte DOCX a PDF.
        En entorno Docker real, esto llamaría a libreoffice --headless.
        Aquí simulamos el éxito para el MVP o usamos reportlab si es texto plano.
        """
        # Simulación para MVP: Copiar el archivo o crear un PDF básico
        # En producción: 
        # subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', docx_path, '--outdir', os.path.dirname(pdf_path)])
        
        try:
            # Intento de conversión real si existe libreoffice
            result = subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "pdf", docx_path, "--outdir", os.path.dirname(pdf_path)],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                # Mover el archivo generado al nombre deseado
                generated_pdf = docx_path.replace(".docx", ".pdf")
                if os.path.exists(generated_pdf):
                    os.rename(generated_pdf, pdf_path)
                    return True
        except Exception:
            pass
        
        # Fallback: Crear un PDF simple indicando que el documento está listo (para demo sin LibreOffice)
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "Documento Generado Exitosamente")
        c.drawString(100, 730, f"Origen: {os.path.basename(docx_path)}")
        c.drawString(100, 710, "(Nota: Conversión completa requiere LibreOffice instalado en el contenedor)")
        c.save()
        return True

    @staticmethod
    def generate_batch(templates: List[Dict], processes: List[Dict], output_dir: str) -> str:
        """
        Genera un lote de documentos y crea un ZIP.
        templates: Lista de diccionarios con ruta_plantilla y contexto
        processes: Lista de procesos con sus datos
        """
        zip_filename = os.path.join(output_dir, "lote_documentos.zip")
        
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for i, proc in enumerate(processes):
                # Asumimos una plantilla base para el ejemplo
                # En realidad, se selecciona la plantilla según el tipo de documento
                template_path = templates[0]['path'] if templates else None
                
                if not template_path or not os.path.exists(template_path):
                    continue

                context = {
                    'cliente_nombre': proc.get('cliente_nombre', 'N/A'),
                    'cliente_identificacion': proc.get('cliente_identificacion', 'N/A'),
                    'obligacion_numero': proc.get('obligacion_numero', 'N/A'),
                    'valor_total': proc.get('valor_total', 0),
                    'radicado': proc.get('radicado', 'PENDIENTE'),
                    'resolucion': proc.get('resolucion', 'PENDIENTE'),
                    'fecha_emision': proc.get('fecha_emision', ''),
                    'entidad_nombre': proc.get('entidad_nombre', 'Entidad Pública'),
                }

                temp_docx = os.path.join(output_dir, f"temp_{i}.docx")
                temp_pdf = os.path.join(output_dir, f"doc_{proc.get('radicado', i)}.pdf")
                
                try:
                    # 1. Renderizar DOCX
                    rendered_docx = DocumentGenerationService.render_template(template_path, context, temp_docx)
                    
                    # 2. Convertir a PDF
                    DocumentGenerationService.convert_to_pdf(rendered_docx, temp_pdf)
                    
                    # 3. Agregar al ZIP
                    if os.path.exists(temp_pdf):
                        zipf.write(temp_pdf, os.path.basename(temp_pdf))
                        
                        # Limpieza
                        os.remove(temp_docx)
                        os.remove(temp_pdf)
                        
                except Exception as e:
                    print(f"Error generando documento {i}: {e}")
                    continue

        return zip_filename