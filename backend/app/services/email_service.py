"""
Servicio para envío de correos electrónicos
Utiliza plantillas y variables dinámicas
"""
import smtplib
from html import escape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from jinja2 import Template

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
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str = None
    ) -> bool:
        """Envía un correo electrónico"""
        if not from_email:
            from_email = smtp_user
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Adjuntar contenido HTML
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        try:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
            server.quit()
            return True
        except Exception:
            return False

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
