# views/appointments_list.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from ..models import Appointment

@login_required
def my_appointments_view(request):
    """Vue pour afficher tous les rendez-vous de l'utilisatrice"""
    user = request.user
    
    now = timezone.now()
    
    # ✅ CORRIGÉ : Rendez-vous à venir (futurs) - filtrage uniquement par user
    upcoming_appointments = Appointment.objects.filter(
        user=user,
        scheduled_date__gte=now
    ).order_by('scheduled_date')
    
    # ✅ CORRIGÉ : Rendez-vous passés (historique) - filtrage uniquement par user
    past_appointments = Appointment.objects.filter(
        user=user,
        scheduled_date__lt=now
    ).order_by('-scheduled_date')
    
    # Formatage des rendez-vous (inchangé)
    formatted_upcoming = []
    for apt in upcoming_appointments:
        formatted_upcoming.append({
            'id': apt.id,
            'doctor_name': apt.doctor.name if apt.doctor else 'Non assigné',
            'hospital_name': apt.hospital.name if apt.hospital else 'Non assigné',
            'date': apt.scheduled_date.strftime('%d/%m/%Y'),
            'time': apt.scheduled_date.strftime('%H:%M'),
            'type': apt.ultrasound_type or 'Consultation',
            'status': apt.get_status_display() if hasattr(apt, 'get_status_display') else 'Confirmé',
            'registration_number': str(apt.registration_number)[:8] if apt.registration_number else '',
            'is_upcoming': True,
        })
    
    formatted_past = []
    for apt in past_appointments:
        formatted_past.append({
            'id': apt.id,
            'doctor_name': apt.doctor.name if apt.doctor else 'Non assigné',
            'hospital_name': apt.hospital.name if apt.hospital else 'Non assigné',
            'date': apt.scheduled_date.strftime('%d/%m/%Y'),
            'time': apt.scheduled_date.strftime('%H:%M'),
            'type': apt.ultrasound_type or 'Consultation',
            'status': apt.get_status_display() if hasattr(apt, 'get_status_display') else 'Terminé',
            'registration_number': str(apt.registration_number)[:8] if apt.registration_number else '',
            'is_upcoming': False,
        })
    
    context = {
        'upcoming_appointments': formatted_upcoming,
        'past_appointments': formatted_past,
        'upcoming_count': upcoming_appointments.count(),
        'past_count': past_appointments.count(),
        'total_count': upcoming_appointments.count() + past_appointments.count(),
    }
    
    return render(request, 'mapli/my_appointments.html', context)