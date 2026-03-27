# mail.py
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.validators import EmailValidator, ValidationError

from ..email_utils import email_backend_delivers_to_internet
from .receipts import generate_appointment_receipt

logger = logging.getLogger(__name__)

def send_appointment_confirmation_email(appointment):
    """
    Envoie l'email de confirmation avec le PDF (une fois par rendez-vous).

    Returns:
        tuple[bool, str]: (succès livraison Internet, message d'erreur ou "")
    """
    try:
        if getattr(appointment, "receipt_sent", False):
            return True, ""

        display_date = appointment.appointment_date
        if display_date is None and appointment.scheduled_date:
            display_date = (
                appointment.scheduled_date.date()
                if hasattr(appointment.scheduled_date, "date")
                else appointment.scheduled_date
            )

        subject = (
            f"MaPli — Confirmation rendez-vous échographie — {appointment.registration_number}"
        )
        
        # Message HTML
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #0d6efd; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info-box {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .footer {{ background: #343a40; color: white; padding: 15px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 MaPli - Confirmation de Rendez-vous</h1>
            </div>
            
            <div class="content">
                <p>Bonjour <strong>{appointment.patient_name}</strong>,</p>
                
                <p>Votre demande de rendez-vous pour une échographie a été confirmée avec succès.</p>
                
                <div class="info-box">
                    <h3>📅 Détails de votre rendez-vous :</h3>
                    <p><strong>Date :</strong> {display_date.strftime('%d/%m/%Y') if display_date else '—'}</p>
                    <p><strong>Heure prévue :</strong> {appointment.scheduled_date.strftime('%H:%M') if appointment.scheduled_date else '—'}</p>
                    <p><strong>Hôpital :</strong> {appointment.hospital.name}</p>
                    <p><strong>Médecin :</strong> Dr. {appointment.doctor.name}</p>
                    <p><strong>Votre position :</strong> {appointment.daily_sequence}/20</p>
                    <p><strong>Montant :</strong> {appointment.get_formatted_price()}</p>
                    <p><strong>Numéro de confirmation :</strong> {appointment.registration_number}</p>
                </div>
                
                <p><strong>📎 Votre reçu PDF est attaché à cet email.</strong></p>
                
                <h3>📋 Instructions importantes :</h3>
                <ul>
                    <li>Présentez ce reçu à l'accueil de l'hôpital</li>
                    <li>Arrivez 15 minutes avant l'heure de consultation</li>
                    <li>Paiement sur place le jour du rendez-vous</li>
                    <li>Apportez votre carte d'identité</li>
                </ul>
                
                <p>En cas de question, contactez-nous au <strong>+225 07 07 07 07 07</strong></p>
            </div>
            
            <div class="footer">
                <p>MaPli &copy; 2025 - Votre santé, notre priorité</p>
            </div>
        </body>
        </html>
        """
        
        # Générer le PDF
        pdf_content = generate_appointment_receipt(appointment)
        
        plain = (
            f"Bonjour {appointment.patient_name},\n\n"
            f"Votre rendez-vous pour une échographie est confirmé.\n"
            f"Date : {display_date.strftime('%d/%m/%Y') if display_date else '—'}\n"
            f"Heure : {appointment.scheduled_date.strftime('%H:%M') if appointment.scheduled_date else '—'}\n"
            f"Hôpital : {appointment.hospital.name}\n"
            f"Médecin : Dr. {appointment.doctor.name}\n"
            f"Numéro : {appointment.registration_number}\n\n"
            f"Votre reçu PDF est en pièce jointe.\n"
            f"— MaPli\n"
        )

        recipient = (appointment.patient_email or "").strip().lower()
        if not recipient:
            return False, "Adresse e-mail destinataire vide."
        try:
            EmailValidator()(recipient)
        except ValidationError as exc:
            err = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            return False, f"Adresse e-mail invalide : {err}"

        mail_kwargs = {
            "subject": subject,
            "body": plain,
            "from_email": settings.DEFAULT_FROM_EMAIL,
            "to": [recipient],
            "headers": {
                # Aide les filtres à classer le message comme notification transactionnelle (RFC 3834).
                "Auto-Submitted": "auto-generated",
            },
        }
        if settings.DEFAULT_FROM_EMAIL:
            mail_kwargs["reply_to"] = [settings.DEFAULT_FROM_EMAIL]
        bcc_list = [
            addr
            for addr in getattr(settings, "EMAIL_CONFIRMATION_BCC", []) or []
            if addr and addr != recipient
        ]
        if bcc_list:
            mail_kwargs["bcc"] = bcc_list
        email = EmailMultiAlternatives(**mail_kwargs)
        email.attach_alternative(html_message, "text/html")
        email.attach(
            f"recu_echographie_{appointment.registration_number}.pdf",
            pdf_content,
            "application/pdf",
        )
        email.send()

        if not email_backend_delivers_to_internet():
            msg = (
                f"Backend {settings.EMAIL_BACKEND!r} : pas d'envoi Internet "
                "(ajoutez EMAIL_HOST_USER et EMAIL_HOST_PASSWORD dans .env, ou lisez la console du serveur)."
            )
            logger.warning(msg)
            return False, msg

        logger.info(
            "Email de confirmation RDV transmis via SMTP (To=%s, bcc=%s, backend=%s, rdv_id=%s)",
            recipient,
            bcc_list if bcc_list else "—",
            settings.EMAIL_BACKEND,
            appointment.pk,
        )
        appointment.receipt_sent = True
        appointment.save(update_fields=["receipt_sent"])
        return True, ""

    except Exception as e:
        logger.exception("Erreur envoi email confirmation RDV: %s", e)
        err = str(e).strip() or e.__class__.__name__
        return False, err

# Fonction de secours pour compatibilité (si d'autres parties du code l'appellent)
def generate_pdf_receipt(appointment):
    """Fonction de compatibilité - utilise la nouvelle fonction"""
    from .receipts import generate_appointment_receipt
    return generate_appointment_receipt(appointment)