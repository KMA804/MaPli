from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date
from ..models import CustomUser, PregnancyCalendar, PregnancyMilestone, PregnancySymptom, PregnancyChecklist, Appointment

@login_required
def pregnancy_calendar_view(request):
    """Vue principale du calendrier de grossesse"""
    user = request.user
    
    # Vérifier si l'utilisatrice est enceinte
    if not user.is_pregnant:
        messages.warning(request, 'Vous devez indiquer que vous êtes enceinte pour accéder au calendrier.')
        return redirect('profile')
    
    # Récupérer ou créer les entrées du calendrier pour toutes les semaines
    weeks_data = []
    current_week = user.current_pregnancy_week or 1
    
    # Semaines de grossesse (1 à 42)
    for week in range(1, 43):
        calendar_entry, created = PregnancyCalendar.objects.get_or_create(
            user=user,
            week_number=week,
            defaults={
                'is_current': (week == current_week),
                'start_date': calculate_week_start_date(user, week),
                'end_date': calculate_week_end_date(user, week),
            }
        )
        
        # Mettre à jour la semaine en cours si nécessaire
        if week == current_week and not calendar_entry.is_current:
            calendar_entry.is_current = True
            calendar_entry.save()
        elif week != current_week and calendar_entry.is_current:
            calendar_entry.is_current = False
            calendar_entry.save()
        
        # Récupérer les jalons pour cette semaine
        milestones = PregnancyMilestone.objects.filter(week_number=week)
        
        # Vérifier si des rendez-vous sont programmés pour cette semaine
        appointments = Appointment.objects.filter(
            user=user,
            scheduled_date__gte=calendar_entry.start_date if calendar_entry.start_date else date.today(),
            scheduled_date__lte=calendar_entry.end_date if calendar_entry.end_date else date.today() + timedelta(days=7)
        )
        
        weeks_data.append({
            'week': week,
            'entry': calendar_entry,
            'milestones': milestones,
            'has_appointments': appointments.exists(),
            'appointments': appointments,
            'is_past': calendar_entry.end_date and calendar_entry.end_date < date.today() if calendar_entry.end_date else False,
            'is_current': calendar_entry.is_current,
        })
    
    # Récupérer les symptômes récents
    recent_symptoms = PregnancySymptom.objects.filter(
        user=user,
        week_number=current_week
    ).order_by('-date')[:5]
    
    # Récupérer la checklist pour les semaines à venir
    upcoming_tasks = PregnancyChecklist.objects.filter(
        user=user,
        week_number__gte=current_week,
        week_number__lte=current_week + 4,
        is_done=False
    ).order_by('week_number')
    
    context = {
        'weeks_data': weeks_data,
        'current_week': current_week,
        'total_weeks': 42,
        'progress_percentage': (current_week / 42) * 100,
        'recent_symptoms': recent_symptoms,
        'upcoming_tasks': upcoming_tasks,
        'due_date': calculate_due_date(user),
    }
    
    return render(request, 'mapli/pregnancy_calendar.html', context)


@login_required
def update_pregnancy_week_ajax(request):
    """Mise à jour de la semaine de grossesse via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            new_week = int(request.POST.get('week'))
            user = request.user
            
            # Vérifier que la semaine est valide
            if 1 <= new_week <= 42:
                # Mettre à jour l'utilisateur
                old_week = user.current_pregnancy_week
                user.current_pregnancy_week = new_week
                user.save()
                
                # Mettre à jour le calendrier
                # Ancienne semaine en cours -> plus en cours
                if old_week:
                    try:
                        old_entry = PregnancyCalendar.objects.get(user=user, week_number=old_week)
                        old_entry.is_current = False
                        old_entry.save()
                    except PregnancyCalendar.DoesNotExist:
                        pass
                
                # Nouvelle semaine en cours
                new_entry, created = PregnancyCalendar.objects.get_or_create(
                    user=user,
                    week_number=new_week,
                    defaults={'is_current': True}
                )
                if not created:
                    new_entry.is_current = True
                    new_entry.save()
                
                # Vérifier si des jalons doivent être marqués comme complétés
                check_and_complete_milestones(user, new_week)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Semaine mise à jour : {new_week}',
                    'new_week': new_week,
                    'progress': (new_week / 42) * 100
                })
            else:
                return JsonResponse({'success': False, 'error': 'Semaine invalide'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Requête invalide'})


@login_required
def week_detail_view(request, week_number):
    """Vue détaillée d'une semaine spécifique"""
    user = request.user
    calendar_entry = get_object_or_404(PregnancyCalendar, user=user, week_number=week_number)
    
    # Récupérer les données spécifiques à cette semaine
    milestones = PregnancyMilestone.objects.filter(week_number=week_number)
    symptoms = PregnancySymptom.objects.filter(user=user, week_number=week_number)
    tasks = PregnancyChecklist.objects.filter(user=user, week_number=week_number)
    appointments = Appointment.objects.filter(
        user=user,
        scheduled_date__gte=calendar_entry.start_date if calendar_entry.start_date else date.today(),
        scheduled_date__lte=calendar_entry.end_date if calendar_entry.end_date else date.today() + timedelta(days=7)
    )
    
    context = {
        'week': calendar_entry,
        'week_number': week_number,
        'milestones': milestones,
        'symptoms': symptoms,
        'tasks': tasks,
        'appointments': appointments,
        'is_current': calendar_entry.is_current,
    }
    
    return render(request, 'mapli/week_detail.html', context)


@login_required
def add_symptom_view(request):
    """Ajouter un symptôme via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            user = request.user
            week_number = int(request.POST.get('week_number'))
            symptom_type = request.POST.get('symptom_type')
            severity = int(request.POST.get('severity', 1))
            description = request.POST.get('description', '')
            
            symptom = PregnancySymptom.objects.create(
                user=user,
                week_number=week_number,
                symptom_type=symptom_type,
                severity=severity,
                description=description
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Symptôme ajouté',
                'symptom': {
                    'id': symptom.id,
                    'type': symptom.get_symptom_type_display(),
                    'severity': severity,
                    'date': symptom.date.strftime('%d/%m/%Y')
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Requête invalide'})


@login_required
def toggle_task_view(request, task_id):
    """Marquer une tâche comme faite/non faite"""
    if request.method == 'POST':
        try:
            task = get_object_or_404(PregnancyChecklist, id=task_id, user=request.user)
            task.is_done = not task.is_done
            task.done_at = timezone.now() if task.is_done else None
            task.save()
            
            return JsonResponse({
                'success': True,
                'is_done': task.is_done
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Requête invalide'})


# Fonctions utilitaires
def calculate_week_start_date(user, week_number):
    """Calcule la date de début d'une semaine de grossesse"""
    if not user.last_menstrual_period:
        return None
    
    # La grossesse commence à la date des dernières règles
    start_date = user.last_menstrual_period + timedelta(weeks=week_number-1)
    return start_date


def calculate_week_end_date(user, week_number):
    """Calcule la date de fin d'une semaine de grossesse"""
    start = calculate_week_start_date(user, week_number)
    if start:
        return start + timedelta(days=6)
    return None


def calculate_due_date(user):
    """Calcule la date prévue d'accouchement"""
    if user.last_menstrual_period:
        return user.last_menstrual_period + timedelta(days=280)
    elif user.current_pregnancy_week:
        conception_date = timezone.now().date() - timedelta(weeks=user.current_pregnancy_week-2)
        return conception_date + timedelta(days=266)
    return None


def check_and_complete_milestones(user, week_number):
    """Vérifie et marque les jalons comme complétés"""
    milestones = PregnancyMilestone.objects.filter(week_number=week_number)
    for milestone in milestones:
        # Vérifier si le jalon doit être marqué comme complété
        # Par exemple, si c'est un jalon automatique comme "Début du 2ème trimestre"
        if milestone.title.startswith("Début du") or "échographie" in milestone.title.lower():
            milestone.is_completed = True
            milestone.completed_at = timezone.now()
            milestone.save()