# mail.py
from django.core.mail import EmailMessage
from django.conf import settings
from .receipts import generate_appointment_receipt  # Import de la nouvelle fonction

def send_appointment_confirmation_email(appointment):
    """Envoie l'email de confirmation avec le PDF - VERSION CORRIGÉE"""
    try:
        subject = f"📄 Votre reçu de rendez-vous échographie - {appointment.registration_number}"
        
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
                    <p><strong>Date :</strong> {appointment.appointment_date.strftime('%d/%m/%Y')}</p>
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
        
        # Préparer l'email
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[appointment.patient_email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        email.content_subtype = "html"  # Email en HTML
        
        # Attacher le PDF
        email.attach(
            f"recu_echographie_{appointment.registration_number}.pdf",
            pdf_content,
            "application/pdf"
        )
        
        # Envoyer l'email
        email.send()
        
        # Marquer comme envoyé
        appointment.receipt_sent = True
        appointment.save(update_fields=['receipt_sent'])
        
        print(f"✅ Email envoyé à {appointment.patient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email: {str(e)}")
        return False

# Fonction de secours pour compatibilité (si d'autres parties du code l'appellent)
def generate_pdf_receipt(appointment):
    """Fonction de compatibilité - utilise la nouvelle fonction"""
    from .receipts import generate_appointment_receipt
    return generate_appointment_receipt(appointment)