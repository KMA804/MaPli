# views/auth_views.py - Vues d'authentification et dashboard
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

from ..forms import CustomUserCreationForm, LoginForm
from ..models import (
    UserProfile, Patient, CustomUser, Appointment, UserRoles, 
    Hospital, Doctor, Fonctionnalite, HospitalProfile, DoctorProfile
)


# ========================================================
# VUES DU TABLEAU DE BORD PATIENT
# ========================================================

@login_required
def dashboard_view(request):
    """
    Vue pour le tableau de bord utilisateur (patients)
    Affiche les données de grossesse, rendez-vous, rappels et activités récentes
    """
    user = request.user
    
    # 1. DONNÉES DE GROSSESSE
    pregnancy_data = get_pregnancy_data(user)
    
    # 2. RENDEZ-VOUS
    now = timezone.now()
    upcoming_appointments, past_appointments, upcoming_count, next_appointment = get_appointments_data(user, now)
    
    # 3. STATISTIQUES
    stats = get_user_statistics(user)
    
    # 4. RAPPELS PERSONNALISÉS
    reminders = get_personalized_reminders(user, pregnancy_data, next_appointment, now)
    
    # 5. ACTIVITÉ RÉCENTE
    recent_activity = get_recent_activity(user, now, upcoming_appointments)
    
    context = {
        'user': user,
        'pregnancy': pregnancy_data,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'next_appointment': next_appointment,
        'upcoming_count': upcoming_count,
        'stats': stats,
        'reminders': reminders,
        'recent_activity': recent_activity,
        'now': now,
    }
    
    return render(request, 'mapli/dashboard.html', context)


def get_pregnancy_data(user):
    """Calcule les données de grossesse pour un utilisateur"""
    pregnancy_data = {
        'is_pregnant': False,
        'current_week': 0,
        'total_weeks': 40,
        'weeks_left': 0,
        'progress_percentage': 0,
        'due_date': None,
        'trimester': 0,
    }
    
    if user.is_pregnant and user.current_pregnancy_week:
        try:
            current_week = int(user.current_pregnancy_week)
        except (ValueError, TypeError):
            current_week = 0
        
        total_weeks = 40
        weeks_left = max(0, total_weeks - current_week)
        progress_percentage = (current_week / total_weeks * 100) if current_week > 0 else 0
        
        # Calcul du trimestre
        if current_week <= 13:
            trimester = 1
        elif current_week <= 26:
            trimester = 2
        else:
            trimester = 3
        
        # Calcul de la date prévue d'accouchement
        due_date = None
        if user.last_menstrual_period:
            due_date = user.last_menstrual_period + timedelta(days=280)
        elif current_week > 0:
            conception_date = timezone.now().date() - timedelta(weeks=current_week-2)
            due_date = conception_date + timedelta(days=266)
        
        pregnancy_data = {
            'is_pregnant': True,
            'current_week': current_week,
            'total_weeks': total_weeks,
            'weeks_left': weeks_left,
            'progress_percentage': round(progress_percentage, 1),
            'due_date': due_date,
            'trimester': trimester,
        }
    
    return pregnancy_data


def get_appointments_data(user, now):
    """Récupère et formate les rendez-vous de l'utilisateur"""
    # Requêtes de base avec double filtrage (user ou email)
    base_query = Q(user=user) | Q(patient_email=user.email)
    
    # Rendez-vous à venir
    upcoming = Appointment.objects.filter(
        base_query,
        scheduled_date__gte=now
    ).order_by('scheduled_date')[:5]
    
    # Rendez-vous passés
    past = Appointment.objects.filter(
        base_query,
        scheduled_date__lt=now
    ).order_by('-scheduled_date')[:5]
    
    # Nombre de rendez-vous à venir
    upcoming_count = Appointment.objects.filter(
        base_query,
        scheduled_date__gte=now
    ).count()
    
    # Prochain rendez-vous
    next_appointment = upcoming.first() if upcoming.exists() else None
    
    # Formatage des rendez-vous pour l'affichage
    formatted_upcoming = []
    for apt in upcoming:
        formatted_upcoming.append({
            'id': apt.id,
            'doctor_name': apt.doctor.name if apt.doctor else 'Non assigné',
            'hospital_name': apt.hospital.name if apt.hospital else 'Non assigné',
            'date': apt.scheduled_date.strftime('%d'),
            'month': apt.scheduled_date.strftime('%b'),
            'time': apt.scheduled_date.strftime('%H:%M'),
            'type': apt.ultrasound_type or 'Consultation',
            'status': apt.get_status_display() if hasattr(apt, 'get_status_display') else 'Confirmé',
            'registration_number': str(apt.registration_number).split('-')[0] if apt.registration_number else '',
            'is_today': apt.scheduled_date.date() == now.date(),
            'is_tomorrow': apt.scheduled_date.date() == (now + timedelta(days=1)).date(),
        })
    
    return formatted_upcoming, past, upcoming_count, next_appointment


def get_user_statistics(user):
    """Calcule les statistiques de l'utilisateur"""
    base_query = Q(user=user) | Q(patient_email=user.email)
    now = timezone.now()
    
    return {
        'total_appointments': Appointment.objects.filter(base_query).count(),
        'upcoming_appointments': Appointment.objects.filter(base_query, scheduled_date__gte=now).count(),
        'completed_appointments': Appointment.objects.filter(base_query, scheduled_date__lt=now).count(),
        'hospitals_visited': Appointment.objects.filter(base_query).exclude(hospital__isnull=True).values('hospital').distinct().count(),
        'doctors_consulted': Appointment.objects.filter(base_query).exclude(doctor__isnull=True).values('doctor').distinct().count(),
    }


def get_personalized_reminders(user, pregnancy_data, next_appointment, now):
    """Génère des rappels personnalisés pour l'utilisateur"""
    reminders = []
    
    # Rappels liés à la grossesse
    if pregnancy_data['is_pregnant']:
        week = pregnancy_data['current_week']
        
        # Échographie 1er trimestre (11-14 SA)
        if 11 <= week <= 14:
            reminders.append({
                'title': 'Échographie du 1er trimestre',
                'description': 'L\'échographie de datation est recommandée entre 11 et 14 SA',
                'deadline': 'À programmer bientôt',
                'icon': 'heart-pulse',
                'color': 'danger',
                'action_url': '/appoint/',
                'action_text': 'Prendre RDV'
            })
        # Échographie 2ème trimestre (20-22 SA)
        elif 20 <= week <= 22:
            reminders.append({
                'title': 'Échographie morphologique',
                'description': 'L\'échographie du 2ème trimestre est idéale entre 20 et 22 SA',
                'deadline': 'Période idéale',
                'icon': 'heart-pulse',
                'color': 'danger',
                'action_url': '/appoint/',
                'action_text': 'Prendre RDV'
            })
        # Échographie 3ème trimestre (30-32 SA)
        elif 30 <= week <= 32:
            reminders.append({
                'title': 'Échographie de croissance',
                'description': 'L\'échographie du 3ème trimestre est recommandée entre 30 et 32 SA',
                'deadline': 'À venir',
                'icon': 'heart-pulse',
                'color': 'warning',
                'action_url': '/appoint/',
                'action_text': 'Voir disponibilités'
            })
    
    # Rappel pour rendez-vous imminent
    if next_appointment:
        days_until = (next_appointment.scheduled_date.date() - now.date()).days
        if days_until <= 7:
            doctor_name = next_appointment.doctor.name if next_appointment.doctor else 'le médecin'
            reminders.append({
                'title': 'Rendez-vous imminent',
                'description': f"Vous avez rendez-vous avec Dr. {doctor_name} dans {days_until} jour(s)",
                'deadline': f"Dans {days_until} jour(s)",
                'icon': 'calendar-check',
                'color': 'info',
                'action_url': f"/appointment/success/{next_appointment.id}/",
                'action_text': 'Voir détails'
            })
    
    # Rappel pour profil incomplet
    if not user.phone_number or not user.date_of_birth:
        reminders.append({
            'title': 'Profil incomplet',
            'description': 'Complétez votre profil pour un meilleur suivi',
            'deadline': 'À faire',
            'icon': 'person-gear',
            'color': 'warning',
            'action_url': '/api/user/profile/',
            'action_text': 'Compléter'
        })
    
    return reminders


def get_recent_activity(user, now, upcoming_appointments):
    """Génère la liste des activités récentes"""
    recent_activity = []
    
    # Derniers rendez-vous passés
    recent_past = Appointment.objects.filter(
        Q(user=user) | Q(patient_email=user.email),
        scheduled_date__lt=now
    ).order_by('-scheduled_date')[:3]
    
    for apt in recent_past:
        doctor_name = apt.doctor.name if apt.doctor else 'Médecin'
        hospital_name = apt.hospital.name if apt.hospital else 'Hôpital'
        consultation_type = apt.ultrasound_type or 'Consultation'
        
        recent_activity.append({
            'title': f"Rendez-vous avec Dr. {doctor_name}",
            'date': apt.scheduled_date,
            'icon': 'calendar-check',
            'color': 'primary',
            'details': f"{hospital_name} - {consultation_type}"
        })
    
    # Message de bienvenue si aucune activité
    if not recent_activity and not upcoming_appointments:
        recent_activity.append({
            'title': "Bienvenue sur MaPli",
            'date': timezone.now(),
            'icon': 'star',
            'color': 'warning',
            'details': "Commencez par prendre votre premier rendez-vous"
        })
    
    return recent_activity


# ========================================================
# VUES D'AUTHENTIFICATION
# ========================================================

def register_view(request):
    """Page de choix du type d'inscription"""
    return render(request, 'mapli/register/choose.html')

def login_view(request):
    """Connexion unifiée pour tous les utilisateurs"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {user.first_name or user.username} !')
                
                # Redirection selon le rôle
                if user.role == UserRoles.ADMIN_SYSTEME:
                    return redirect('admin_dashboard')
                elif user.role == UserRoles.HOPITAL:
                    return redirect('hospital_dashboard')
                elif user.role == UserRoles.MEDECIN:
                    return redirect('doctor_dashboard')
                else:  # PATIENT
                    return redirect('dashboard')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = LoginForm()
    
    return render(request, 'mapli/index.html', {'form': form})

@login_required
def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('index')


# ========================================================
# VUES POUR ADMINISTRATEUR SYSTÈME (A)
# ========================================================

@login_required
def admin_dashboard(request):
    """Dashboard pour administrateur système"""
    # Vérification du rôle
    if request.user.role != UserRoles.ADMIN_SYSTEME:
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')
    
    # Statistiques globales
    total_users = CustomUser.objects.count()
    new_users_today = CustomUser.objects.filter(
        date_joined__date=timezone.now().date()
    ).count()
    
    active_clients = CustomUser.objects.filter(
        role=UserRoles.PATIENT,
        is_active=True
    ).count()
    inactive_clients = CustomUser.objects.filter(
        role=UserRoles.PATIENT,
        is_active=False
    ).count()
    
    total_hospitals = Hospital.objects.count()
    total_doctors = Doctor.objects.count()
    verified_hospitals = Hospital.objects.filter(is_active=True).count()
    verified_doctors = Doctor.objects.filter(is_active=True).count()
    
    # Fonctionnalités
    features = Fonctionnalite.objects.annotate(
        clients_count=Count('profils')
    )
    
    # Derniers utilisateurs
    recent_users = CustomUser.objects.all().order_by('-date_joined')[:10]
    for user in recent_users:
        if user.role == UserRoles.ADMIN_SYSTEME:
            user.role_color = 'danger'
        elif user.role == UserRoles.HOPITAL:
            user.role_color = 'success'
        elif user.role == UserRoles.MEDECIN:
            user.role_color = 'warning'
        else:
            user.role_color = 'primary'
    
    context = {
        'user': request.user,
        'total_users': total_users,
        'new_users_today': new_users_today,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'total_hospitals': total_hospitals,
        'total_doctors': total_doctors,
        'verified_hospitals': verified_hospitals,
        'verified_doctors': verified_doctors,
        'features': features,
        'recent_users': recent_users,
    }
    
    return render(request, 'mapli/admin/dashboard.html', context)


# ========================================================
# VUES POUR HÔPITAL
# ========================================================

@login_required
def hospital_dashboard(request):
    """Dashboard pour hôpital"""
    if request.user.role != UserRoles.HOPITAL:
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')
    
    # Récupérer l'hôpital associé à cet utilisateur
    hospital = None
    try:
        if hasattr(request.user, 'hospital_profile'):
            hospital = request.user.hospital_profile.hospital
    except:
        hospital = None
    
    # Statistiques pour l'hôpital
    if hospital:
        total_doctors = hospital.doctors.count()
        total_appointments = Appointment.objects.filter(hospital=hospital).count()
        pending_appointments = Appointment.objects.filter(hospital=hospital, status='PE').count()
    else:
        total_doctors = 0
        total_appointments = 0
        pending_appointments = 0
    
    context = {
        'user': request.user,
        'hospital': hospital,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
    }
    return render(request, 'mapli/hospital/dashboard.html', context)


# ========================================================
# VUES POUR MÉDECIN
# ========================================================

@login_required
def doctor_dashboard(request):
    """Dashboard pour médecin"""
    if request.user.role != UserRoles.MEDECIN:
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')
    
    # Récupérer le médecin associé à cet utilisateur
    doctor = None
    try:
        if hasattr(request.user, 'doctor_profile'):
            doctor = request.user.doctor_profile.doctor
    except:
        doctor = None
    
    # Statistiques pour le médecin
    if doctor:
        today = timezone.now().date()
        total_appointments = Appointment.objects.filter(doctor=doctor).count()
        today_appointments = Appointment.objects.filter(
            doctor=doctor, 
            scheduled_date__date=today
        ).count()
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor, 
            scheduled_date__gte=timezone.now()
        ).count()
    else:
        total_appointments = 0
        today_appointments = 0
        upcoming_appointments = 0
    
    context = {
        'user': request.user,
        'doctor': doctor,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
    }
    return render(request, 'mapli/doctor/dashboard.html', context)