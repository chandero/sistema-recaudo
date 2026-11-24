"""
Servicio para envío de correos electrónicos
Utiliza plantillas y variables dinámicas
"""
import mimetypes
import smtplib
from html import escape
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from jinja2 import Template

from app.core.logging.logger import get_logger

logger = get_logger(__name__)

class EmailService:
    
    @staticmethod
    def render_template_content(template_html: str, context: Dict[str, Any]) -> str:
        """Renderiza el contenido del correo con variables Jinja2"""
        try:
            tpl = Template(template_html)
            return tpl.render(context)
        except Exception as e:
            raise Exception(f"Error al renderizar plantilla de correo: {str(e)}")

    @staticmethod
    def _adjuntar(msg: MIMEMultipart, nombre: str, contenido: bytes, mimetype: Optional[str] = None) -> None:
        """Adjunta un archivo al correo usando el tipo MIME correcto."""
        tipo_calculado, _ = mimetypes.guess_type(nombre)
        tipo = mimetype or tipo_calculado or "application/octet-stream"
        principal, _, subtipo = tipo.partition("/")
        parte = MIMEBase(principal or "application", subtipo or "octet-stream")
        parte.set_payload(contenido)
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", "attachment", filename=nombre)
        msg.attach(parte)

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Envía un correo electrónico.

        Args:
            attachments: Lista opcional de {'filename', 'content', 'mimetype'},
                con 'content' en bytes.
        """
        if not from_email:
            from_email = smtp_user

        # Un correo con adjuntos debe ser multipart/mixed; 'alternative' solo
        # admite variantes del mismo cuerpo.
        msg = MIMEMultipart('mixed' if attachments else 'alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Adjuntar contenido HTML
        part = MIMEText(html_content, 'html')
        msg.attach(part)

        for adjunto in attachments or []:
            EmailService._adjuntar(
                msg,
                adjunto.get("filename", "documento"),
                adjunto.get("content", b""),
                adjunto.get("mimetype"),
            )
        
        try:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
            server.quit()
            return True
        except Exception as error:
            logger.error(
                module="email",
                action="send_failed",
                message=f"No se pudo enviar el correo a {to_email}: {str(error)}",
                data={"destinatario": to_email, "asunto": subject, "error": str(error)}
            )
            return False

    @staticmethod
    def send_document_email(
        to_email: str,
        subject: str,
        html_content: str,
        attachments: List[Dict[str, Any]],
        smtp_config: Dict[str, Any]
    ) -> bool:
        """Envía un documento generado con sus adjuntos."""
        return EmailService.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            attachments=attachments,
            **smtp_config,
        )

    @staticmethod
    def send_user_invitation(to_email: str, full_name: str, invitation_url: str, smtp_config: Dict[str, Any]) -> bool:
        safe_name = escape(full_name)
        safe_url = escape(invitation_url, quote=True)
        html = f"""
        <h2>Invitación al Sistema de Gestión de Cartera</h2>
        <p>Hola {safe_name},</p>
        <p>Se creó una invitación para que actives tu cuenta.</p>
        <p><a href=\"{safe_url}\">Definir contraseña y activar cuenta</a></p>
        <p>Este enlace es personal, de un solo uso y tiene vencimiento.</p>
        """
        return EmailService.send_email(
            to_email=to_email,
            subject="Invitación al Sistema de Gestión de Cartera",
            html_content=html,
            **smtp_config,
        )

    @staticmethod
    def send_batch_emails(
        recipients: List[Dict],
        template_subject: str,
        template_body: str,
        smtp_config: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Envía correos masivos basados en una plantilla.
        recipients: Lista de diccionarios con 'email' y variables de contexto
        Returns: Estadísticas de envío
        """
        stats = {'success': 0, 'failed': 0}
        
        for recipient in recipients:
            email = recipient.get('email')
            if not email:
                stats['failed'] += 1
                continue
                
            # Renderizar asunto y cuerpo
            try:
                subject_rendered = EmailService.render_template_content(template_subject, recipient)
                body_rendered = EmailService.render_template_content(template_body, recipient)
                
                success = EmailService.send_email(
                    to_email=email,
                    subject=subject_rendered,
                    html_content=body_rendered,
                    **smtp_config
                )
                
                if success:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
            except Exception:
                stats['failed'] += 1
                
        return stats
