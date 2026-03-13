from django.shortcuts import render, get_object_or_404
from .receipts import get_pdf_response
from ..models import Appointment

def appointment_success(request, appointment_id):
    """Page de confirmation après prise de rendez-vous"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Envoyer l'email de confirmation
    from .mail import send_appointment_confirmation_email
    send_appointment_confirmation_email(appointment)
    
    context = {
        'appointment': appointment
    }
    return render(request, 'mapli/appointment_success.html', context)

def download_receipt(request, appointment_id):
    """Téléchargement du reçu PDF"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return get_pdf_response(appointment)