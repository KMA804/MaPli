# views/profile.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q  # ← AJOUTER CET IMPORT
from ..models import Appointment, CustomUser
from datetime import datetime

@login_required
def profile_view(request):
    """Vue pour afficher et modifier le profil utilisateur"""
    user = request.user
    
    if request.method == 'POST':
        # Récupération des données du formulaire (inchangé)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        date_of_birth = request.POST.get('date_of_birth')
        country = request.POST.get('country')
        commune = request.POST.get('commune')
        district = request.POST.get('district')
        job_title = request.POST.get('job_title')
        
        # Données médicales
        blood_type = request.POST.get('blood_type')
        allergies = request.POST.get('allergies')
        is_pregnant = request.POST.get('is_pregnant') == 'on'
        current_pregnancy_week = request.POST.get('current_pregnancy_week')
        last_menstrual_period = request.POST.get('last_menstrual_period')
        
        # Mise à jour des champs
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone_number = phone_number
        if date_of_birth:
            user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        user.country = country
        user.commune = commune
        user.district = district
        user.job_title = job_title
        
        # Mise à jour des données médicales
        user.blood_type = blood_type
        user.allergies = allergies
        user.is_pregnant = is_pregnant
        if current_pregnancy_week:
            user.current_pregnancy_week = int(current_pregnancy_week)
        if last_menstrual_period:
            user.last_menstrual_period = datetime.strptime(last_menstrual_period, '%Y-%m-%d').date()
        
        user.save()
        messages.success(request, 'Votre profil a été mis à jour avec succès !')
        return redirect('profile')
    
    # Statistiques pour le profil - AVEC DOUBLE FILTRAGE
    now = timezone.now()
    
    # ✅ CORRIGÉ : Nombre total de rendez-vous
    total_appointments = Appointment.objects.filter(
        Q(user=user) | Q(patient_email=user.email)  # ← Soit user, soit email
    ).count()
    
    # ✅ CORRIGÉ : Rendez-vous à venir
    upcoming_count = Appointment.objects.filter(
        Q(user=user) | Q(patient_email=user.email),
        scheduled_date__gte=now
    ).count()
    
    # ✅ CORRIGÉ : Rendez-vous passés
    past_count = Appointment.objects.filter(
        Q(user=user) | Q(patient_email=user.email),
        scheduled_date__lt=now
    ).count()
    
    # ✅ CORRIGÉ : Prochain rendez-vous
    next_appointment = Appointment.objects.filter(
        Q(user=user) | Q(patient_email=user.email),
        scheduled_date__gte=now
    ).order_by('scheduled_date').first()
    
    # ✅ CORRIGÉ : Dernier rendez-vous
    last_appointment = Appointment.objects.filter(
        Q(user=user) | Q(patient_email=user.email),
        scheduled_date__lt=now
    ).order_by('-scheduled_date').first()
    
    # Calcul de l'âge (inchangé)
    age = None
    if user.date_of_birth:
        today = timezone.now().date()
        age = today.year - user.date_of_birth.year
        if today.month < user.date_of_birth.month or (today.month == user.date_of_birth.month and today.day < user.date_of_birth.day):
            age -= 1
    
    # Calcul de la date d'accouchement (inchangé)
    due_date = None
    if user.is_pregnant and user.last_menstrual_period:
        due_date = user.last_menstrual_period + timezone.timedelta(days=280)
    elif user.is_pregnant and user.current_pregnancy_week:
        conception_date = timezone.now().date() - timezone.timedelta(weeks=user.current_pregnancy_week-2)
        due_date = conception_date + timezone.timedelta(days=266)
    
    context = {
        'user': user,
        'age': age,
        'due_date': due_date,
        'stats': {
            'total_appointments': total_appointments,
            'upcoming_count': upcoming_count,
            'past_count': past_count,
        },
        'next_appointment': next_appointment,
        'last_appointment': last_appointment,
    }
    
    return render(request, 'mapli/profile.html', context)