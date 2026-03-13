# mapli/views/home.py
from gettext import translation
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import Patient
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    """Vue pour la page d'accueil"""
    return render(request, 'mapli/home.html')

@login_required
def about(request):
    """Vue pour la page À propos"""
    return render(request, 'mapli/about.html')

@login_required
def services(request):
    """Vue pour la page Services"""
    return render(request, 'mapli/services.html')

@login_required
def doctors(request):
    """Vue pour la page Médecins"""
    return render(request, 'mapli/doctors.html')

@login_required
def departments(request):
    """Vue pour la page Départements"""
    return render(request, 'mapli/departments.html')

@login_required
def appointment_view(request):
    """Vue pour la page de prise de rendez-vous"""
    return render(request, 'mapli/appoint.html')
@login_required
def appointment_success(request):
    """Vue pour la page de succès de rendez-vous"""
    return render(request, 'mapli/appointment_success.html')
@login_required
def pregnancy_ultrasound_request(request):
    """Vue pour la page de demande d'échographie de grossesse"""
    return render(request, 'mapli/pregnancy_ultrasound_request.html')
