from django.conf import settings
from django.shortcuts import render, get_object_or_404
from .receipts import get_pdf_response
from ..models import Appointment

def appointment_success(request, appointment_id):
    """Page de confirmation après prise de rendez-vous"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    param = request.GET.get("email_sent")
    if param == "1":
        confirmation_email_sent = True
    elif param == "0":
        confirmation_email_sent = False
    else:
        confirmation_email_sent = appointment.receipt_sent

    context = {
        "appointment": appointment,
        "confirmation_email_sent": confirmation_email_sent,
        "show_dev_email_hint": settings.DEBUG and not confirmation_email_sent,
    }
    return render(request, 'mapli/appointment_success.html', context)

def download_receipt(request, appointment_id):
    """Téléchargement du reçu PDF"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return get_pdf_response(appointment)