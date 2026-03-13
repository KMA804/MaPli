# views.py - Ajoutez cette vue API personnalisée
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import EmailMessage
from .mail import generate_pdf_receipt
import json

@api_view(['POST'])
def create_appointment_with_email(request):
    """Crée un rendez-vous et envoie le reçu PDF par email"""
    try:
        data = request.data
        
        # Simulation de la création du rendez-vous (à adapter avec vos modèles)
        appointment_data = {
            'id': 1,  # Simulé
            'registration_number': 'RDV-2024-001',  # Simulé
            'patient_name': data.get('patient_name'),
            'patient_email': data.get('patient_email'),
            'patient_phone': data.get('patient_phone'),
            'scheduled_date': data.get('scheduled_date'),
            'ultrasound_type': data.get('ultrasound_type'),
            'pregnancy_week': data.get('pregnancy_week'),
            'reason': data.get('reason')
        }
        
        # Générer le PDF (simulation)
        pdf_content = generate_pdf_receipt(appointment_data)
        
        if pdf_content:
            # Envoyer l'email au patient
            send_email_to_patient(
                patient_email=data.get('patient_email'),
                patient_name=data.get('patient_name'),
                appointment_data=appointment_data,
                pdf_content=pdf_content
            )
            
            # ENVOYER UNE COPIE À VOTRE EMAIL DE DÉVELOPPEMENT
            send_copy_to_developer(
                patient_email=data.get('patient_email'),
                patient_name=data.get('patient_name'),
                appointment_data=appointment_data,
                pdf_content=pdf_content
            )
            
            return Response({
                'success': True,
                'message': 'Rendez-vous créé avec succès. Le reçu PDF a été envoyé par email.',
                'registration_number': appointment_data['registration_number']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': 'Erreur lors de la génération du PDF'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Erreur lors de la création du rendez-vous: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

def send_email_to_patient(patient_email, patient_name, appointment_data, pdf_content):
    """Envoie l'email avec le reçu PDF au patient"""
    subject = f"Confirmation de votre rendez-vous d'échographie - {appointment_data['registration_number']}"
    
    message = f"""
    Bonjour {patient_name},
    
    Votre demande de rendez-vous pour une échographie a été enregistrée avec succès.
    
    📋 DÉTAILS DU RENDEZ-VOUS:
    • Numéro d'inscription: {appointment_data['registration_number']}
    • Date et heure: {appointment_data['scheduled_date']}
    • Type d'échographie: {appointment_data['ultrasound_type']}
    • Semaine de grossesse: {appointment_data['pregnancy_week']}
    
    📄 VOTRE REÇU:
    Vous trouverez votre reçu officiel en pièce jointe de cet email.
    
    💳 PROCÉDURE DE PAIEMENT:
    Présentez ce reçu à l'accueil de notre clinique pour effectuer le paiement 
    et confirmer définitivement votre rendez-vous.
    
    ⏰ CONSEIL:
    Merci de vous présenter 15 minutes avant l'heure du rendez-vous.
    
    Pour toute question, contactez-nous au +225 XX XX XX XX XX.
    
    Cordialement,
    L'équipe MaPli Maternité
    """
    
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email='noreply@meditrust.maternite',
        to=[patient_email]
    )
    
    # Attacher le PDF
    email.attach(
        f'recu_rdv_{appointment_data["registration_number"]}.pdf',
        pdf_content,
        'application/pdf'
    )
    
    # Envoyer l'email
    email.send()

def send_copy_to_developer(patient_email, patient_name, appointment_data, pdf_content):
    """Envoie une copie de l'email à votre compte de développement"""
    developer_email = "votre.email@developer.com"  # REMPLACEZ PAR VOTRE EMAIL
    
    subject = f"[COPIE DEV] Rendez-vous échographie - {appointment_data['registration_number']}"
    
    message = f"""
    📧 COPIE POUR DÉVELOPPEMENT - RENDEZ-VOUS CRÉÉ
    
    Patient: {patient_name}
    Email: {patient_email}
    Téléphone: {appointment_data['patient_phone']}
    
    Détails du rendez-vous:
    • Numéro: {appointment_data['registration_number']}
    • Date/Heure: {appointment_data['scheduled_date']}
    • Type: {appointment_data['ultrasound_type']}
    • Semaine: {appointment_data['pregnancy_week']}
    • Motif: {appointment_data['reason']}
    
    ---
    Cet email est une copie envoyée au développeur pour test.
    """
    
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email='dev@meditrust.maternite',
        to=[developer_email]
    )
    
    # Attacher aussi le PDF pour vérification
    email.attach(
        f'DEV_recu_rdv_{appointment_data["registration_number"]}.pdf',
        pdf_content,
        'application/pdf'
    )
    
    email.send()