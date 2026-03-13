# views/dashboard.py - Version corrigée avec filtrage uniquement par user

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import Appointment, CustomUser
from django.db.models import Count  # ← Q supprimé

@login_required
def dashboard_view(request):
    """Vue pour le tableau de bord utilisateur avec données dynamiques"""
    user = request.user
    
    # 1. DONNÉES DE GROSSESSE - directement depuis CustomUser
    pregnancy_data = {}
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
    else:
        pregnancy_data = {
            'is_pregnant': False,
            'current_week': 0,
            'total_weeks': 40,
            'weeks_left': 0,
            'progress_percentage': 0,
            'due_date': None,
            'trimester': 0,
        }
    
    # 2. RENDEZ-VOUS - CORRIGÉ : Filtrage uniquement par user
    now = timezone.now()
    
    # ✅ Rendez-vous à venir (futurs) - uniquement par user
    upcoming_appointments = Appointment.objects.filter(
        user=user,
        scheduled_date__gte=now
    ).order_by('scheduled_date')[:5]
    
    # ✅ Rendez-vous passés - uniquement par user
    past_appointments = Appointment.objects.filter(
        user=user,
        scheduled_date__lt=now
    ).order_by('-scheduled_date')[:5]
    
    # ✅ Compter les rendez-vous à venir - uniquement par user
    upcoming_count = Appointment.objects.filter(
        user=user,
        scheduled_date__gte=now
    ).count()
    
    # Prochain rendez-vous
    next_appointment = upcoming_appointments.first() if upcoming_appointments.exists() else None
    
    # Formatage des rendez-vous pour l'affichage
    formatted_upcoming = []
    for apt in upcoming_appointments:
        formatted_upcoming.append({
            'id': apt.id,
            'doctor_name': apt.doctor.name if apt.doctor else 'Non assigné',
            'hospital_name': apt.hospital.name if apt.hospital else 'Non assigné',
            'date': apt.scheduled_date.strftime('%d'),
            'month': apt.scheduled_date.strftime('%b'),
            'time': apt.scheduled_date.strftime('%H:%M'),
            'type': apt.ultrasound_type or 'Consultation',
            'status': getattr(apt, 'status', 'confirmé'),
            'registration_number': str(apt.registration_number)[:8] if apt.registration_number else '',
            'is_today': apt.scheduled_date.date() == now.date(),
            'is_tomorrow': apt.scheduled_date.date() == (now + timedelta(days=1)).date(),
        })
    
    # 3. STATISTIQUES - uniquement par user
    stats = {
        'total_appointments': Appointment.objects.filter(user=user).count(),
        'upcoming_appointments': upcoming_count,
        'completed_appointments': past_appointments.count(),
        'hospitals_visited': Appointment.objects.filter(
            user=user
        ).exclude(hospital__isnull=True).values('hospital').distinct().count(),
        'doctors_consulted': Appointment.objects.filter(
            user=user
        ).exclude(doctor__isnull=True).values('doctor').distinct().count(),
    }
    
    # 4. RAPPELS PERSONNALISÉS
    reminders = []
    
    # Rappel basé sur la semaine de grossesse
    if pregnancy_data['is_pregnant']:
        week = pregnancy_data['current_week']
        
        # Échographies recommandées
        if week <= 14 and week >= 11:
            reminders.append({
                'title': 'Échographie du 1er trimestre',
                'description': 'L\'échographie de datation est recommandée entre 11 et 14 SA',
                'deadline': 'À programmer bientôt',
                'icon': 'heart-pulse',
                'color': 'danger',
                'action_url': '/appoint/',
                'action_text': 'Prendre RDV'
            })
        elif week <= 22 and week >= 20:
            reminders.append({
                'title': 'Échographie morphologique',
                'description': 'L\'échographie du 2ème trimestre est idéale entre 20 et 22 SA',
                'deadline': 'Période idéale',
                'icon': 'heart-pulse',
                'color': 'danger',
                'action_url': '/appoint/',
                'action_text': 'Prendre RDV'
            })
        elif week <= 32 and week >= 30:
            reminders.append({
                'title': 'Échographie de croissance',
                'description': 'L\'échographie du 3ème trimestre est recommandée entre 30 et 32 SA',
                'deadline': 'À venir',
                'icon': 'heart-pulse',
                'color': 'warning',
                'action_url': '/appoint/',
                'action_text': 'Voir disponibilités'
            })
    
    # Rappel basé sur le prochain rendez-vous
    if next_appointment:
        days_until = (next_appointment.scheduled_date.date() - now.date()).days
        if days_until <= 7:
            reminders.append({
                'title': 'Rendez-vous imminent',
                'description': f"Vous avez rendez-vous avec Dr. {next_appointment.doctor.name if next_appointment.doctor else 'le médecin'} dans {days_until} jour(s)",
                'deadline': f"Dans {days_until} jour(s)",
                'icon': 'calendar-check',
                'color': 'info',
                'action_url': f"/appointment/success/{next_appointment.id}/",
                'action_text': 'Voir détails'
            })
    
    # Rappel profil incomplet
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
    
    # 5. ACTIVITÉ RÉCENTE - uniquement par user
    recent_activity = []
    
    # Ajouter les derniers rendez-vous comme activités
    recent_past = Appointment.objects.filter(
        user=user,
        scheduled_date__lt=now
    ).order_by('-scheduled_date')[:3]
    
    for apt in recent_past:
        recent_activity.append({
            'title': f"Rendez-vous avec Dr. {apt.doctor.name if apt.doctor else 'Médecin'}",
            'date': apt.scheduled_date,
            'icon': 'calendar-check',
            'color': 'primary',
            'details': f"{apt.hospital.name if apt.hospital else 'Hôpital'} - {apt.ultrasound_type or 'Consultation'}"
        })
    
    # Si pas d'activité, ajouter un message de bienvenue
    if not recent_activity and not upcoming_appointments:
        recent_activity.append({
            'title': "Bienvenue sur MaPli",
            'date': timezone.now(),
            'icon': 'star',
            'color': 'warning',
            'details': "Commencez par prendre votre premier rendez-vous"
        })
    
    context = {
        'user': user,
        'pregnancy': pregnancy_data,
        'upcoming_appointments': formatted_upcoming,
        'past_appointments': past_appointments,
        'next_appointment': next_appointment,
        'upcoming_count': upcoming_count,
        'stats': stats,
        'reminders': reminders,
        'recent_activity': recent_activity,
        'now': now,
    }
    
    return render(request, 'mapli/dashboard.html', context)