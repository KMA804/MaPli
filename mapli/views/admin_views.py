# views/admin_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from ..models import CustomUser, UserProfile, Fonctionnalite, Hospital, Doctor, UserRoles, SystemLog, Appointment, PregnancyCalendar
from ..decorators import role_required


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_dashboard(request):
    """Dashboard administrateur système"""
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
        clients_count=Count('customuser')
    )
    
    # Derniers logs (pour le dashboard)
    recent_logs = SystemLog.objects.all().order_by('-created_at')[:10]
    
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
        'recent_logs': recent_logs,
    }
    
    return render(request, 'mapli/admin/dashboard.html', context)


# ========================================================
# VUES POUR LES UTILISATEURS
# ========================================================

@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_users_list(request):
    """Liste des utilisateurs"""
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filtres
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'current_role': role_filter,
        'current_status': status_filter,
        'search_query': search_query,
    }
    return render(request, 'mapli/admin/users_list.html', context)


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_user_detail(request, user_id):
    """Détail d'un utilisateur"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    context = {
        'user_detail': user,
        'appointments': Appointment.objects.filter(user=user).order_by('-scheduled_date')[:10],
    }
    return render(request, 'mapli/admin/user_detail.html', context)


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_user_toggle(request, user_id):
    """Activer/désactiver un utilisateur"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    # Créer un log
    SystemLog.objects.create(
        user=request.user,
        action_type='user_toggle',
        description=f"Utilisateur {user.username} {'activé' if user.is_active else 'désactivé'}",
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    messages.success(request, f"Utilisateur {'activé' if user.is_active else 'désactivé'} avec succès")
    return redirect('admin_users_list')


# ========================================================
# VUES POUR LES PATIENTS (AU LIEU DE CLIENTS)
# ========================================================

@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_patients_list(request):
    """Liste des patients"""
    patients = CustomUser.objects.filter(role=UserRoles.PATIENT)
    features = Fonctionnalite.objects.all()
    
    context = {
        'patients': patients,
        'features': features,
    }
    return render(request, 'mapli/admin/patients_list.html', context)


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_patient_detail(request, patient_id):
    """Détail d'un patient"""
    patient = get_object_or_404(CustomUser, id=patient_id, role=UserRoles.PATIENT)
    
    # Récupérer le profil patient s'il existe
    try:
        patient_profile = patient.patient_profile
    except:
        patient_profile = None
    
    context = {
        'patient': patient,
        'patient_profile': patient_profile,
        'appointments': Appointment.objects.filter(user=patient).order_by('-scheduled_date')[:10],
        'pregnancy_calendar': PregnancyCalendar.objects.filter(user=patient).order_by('week_number'),
    }
    return render(request, 'mapli/admin/patient_detail.html', context)


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_patient_toggle(request, patient_id):
    """Activer/désactiver un patient"""
    patient = get_object_or_404(CustomUser, id=patient_id, role=UserRoles.PATIENT)
    patient.is_active = not patient.is_active
    patient.save()
    
    # Créer un log
    SystemLog.objects.create(
        user=request.user,
        action_type='patient_toggle',
        description=f"Patient {patient.first_name} {patient.last_name} {'activé' if patient.is_active else 'désactivé'}",
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    messages.success(request, f"Patient {'activé' if patient.is_active else 'désactivé'} avec succès")
    return redirect('admin_patients_list')


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_patient_features(request, patient_id):
    """Gérer les fonctionnalités d'un patient"""
    patient = get_object_or_404(CustomUser, id=patient_id, role=UserRoles.PATIENT)
    features = Fonctionnalite.objects.all()
    
    if request.method == 'POST':
        feature_ids = request.POST.getlist('features')
        patient.authorized_features.clear()
        for feature_id in feature_ids:
            feature = get_object_or_404(Fonctionnalite, id=feature_id)
            patient.authorized_features.add(feature)
        
        # Créer un log
        SystemLog.objects.create(
            user=request.user,
            action_type='patient_features',
            description=f"Fonctionnalités mises à jour pour le patient {patient.first_name} {patient.last_name}",
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        messages.success(request, "Fonctionnalités mises à jour avec succès")
        return redirect('admin_patients_list')
    
    # Préparer la liste des IDs des fonctionnalités déjà assignées
    assigned_features = patient.authorized_features.values_list('id', flat=True)
    
    context = {
        'patient': patient,
        'features': features,
        'assigned_features': list(assigned_features),
    }
    return render(request, 'mapli/admin/patient_features.html', context)


# ========================================================
# VUES POUR LES FONCTIONNALITÉS
# ========================================================

@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_features_list(request):
    """Gestion des fonctionnalités"""
    features = Fonctionnalite.objects.annotate(
        clients_count=Count('customuser')
    )
    return render(request, 'mapli/admin/features_list.html', {'features': features})


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_add_feature(request):
    """Ajouter une fonctionnalité"""
    if request.method == 'POST':
        nom = request.POST.get('nom')
        code = request.POST.get('code')
        categorie = request.POST.get('categorie')
        description = request.POST.get('description')
        est_active = request.POST.get('est_active_globalement') == 'on'
        
        Fonctionnalite.objects.create(
            nom=nom,
            code=code,
            categorie=categorie,
            description=description,
            est_active_globalement=est_active
        )
        messages.success(request, 'Fonctionnalité ajoutée avec succès')
    return redirect('admin_features_list')


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_feature_toggle(request, feature_id):
    """Activer/désactiver une fonctionnalité globalement"""
    feature = get_object_or_404(Fonctionnalite, id=feature_id)
    feature.est_active_globalement = not feature.est_active_globalement
    feature.save()
    
    # Créer un log
    SystemLog.objects.create(
        user=request.user,
        action_type='feature_toggle',
        description=f"Fonctionnalité {feature.nom} {'activée' if feature.est_active_globalement else 'désactivée'}",
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    messages.success(request, f"Fonctionnalité {'activée' if feature.est_active_globalement else 'désactivée'}")
    return redirect('admin_features_list')


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_feature_access(request, feature_id):
    """Gérer l'accès des patients à une fonctionnalité"""
    feature = get_object_or_404(Fonctionnalite, id=feature_id)
    patients = CustomUser.objects.filter(role=UserRoles.PATIENT)
    
    if request.method == 'POST':
        patient_ids = request.POST.getlist('patients')
        feature.customuser.clear()
        for patient_id in patient_ids:
            patient = CustomUser.objects.get(id=patient_id)
            feature.customuser.add(patient)
        
        # Créer un log
        SystemLog.objects.create(
            user=request.user,
            action_type='permission_change',
            description=f"Accès à la fonctionnalité {feature.nom} mis à jour pour {len(patient_ids)} patients",
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        messages.success(request, "Accès mis à jour avec succès")
        return redirect('admin_features_list')
    
    # Préparer la liste des IDs des patients déjà autorisés
    authorized_patients = feature.customuser.filter(role=UserRoles.PATIENT).values_list('id', flat=True)
    
    context = {
        'feature': feature,
        'patients': patients,
        'authorized_patients': list(authorized_patients),
    }
    return render(request, 'mapli/admin/feature_access.html', context)


# ========================================================
# VUES POUR LES LOGS SYSTÈME
# ========================================================

@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_logs_list(request):
    """Liste des journaux système"""
    logs = SystemLog.objects.all().order_by('-created_at')
    
    # Filtres
    action_type = request.GET.get('action_type', '')
    if action_type:
        logs = logs.filter(action_type=action_type)
    
    user_id = request.GET.get('user_id', '')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    date_from = request.GET.get('date_from', '')
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    context = {
        'logs': logs,
        'action_types': SystemLog.ACTION_TYPES,
    }
    return render(request, 'mapli/admin/logs_list.html', context)


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_log_detail(request, log_id):
    """Détail d'un journal"""
    log = get_object_or_404(SystemLog, id=log_id)
    return render(request, 'mapli/admin/log_detail.html', {'log': log})


# ========================================================
# VUES POUR HÔPITAUX
# ========================================================

@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_hospitals_list(request):
    """Liste des hôpitaux"""
    hospitals = Hospital.objects.annotate(
        doctors_count=Count('doctors')
    )
    
    active_hospitals = hospitals.filter(is_active=True).count()
    pending_hospitals = hospitals.filter(is_active=False).count()
    hospitals_with_ultrasound = hospitals.filter(has_ultrasound=True).count()
    hospitals_with_maternity = hospitals.filter(has_maternity=True).count()
    
    context = {
        'hospitals': hospitals,
        'active_hospitals': active_hospitals,
        'pending_hospitals': pending_hospitals,
        'hospitals_with_ultrasound': hospitals_with_ultrasound,
        'hospitals_with_maternity': hospitals_with_maternity,
    }
    return render(request, 'mapli/admin/hospitals_list.html', context)


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_hospital_detail(request, hospital_id):
    """Détail d'un hôpital"""
    hospital = get_object_or_404(Hospital, id=hospital_id)
    return render(request, 'mapli/admin/hospital_detail.html', {'hospital': hospital})


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_hospital_toggle(request, hospital_id):
    """Activer/désactiver un hôpital"""
    hospital = get_object_or_404(Hospital, id=hospital_id)
    hospital.is_active = not hospital.is_active
    hospital.save()
    
    # Créer un log
    SystemLog.objects.create(
        user=request.user,
        action_type='hospital_toggle',
        description=f"Hôpital {hospital.name} {'activé' if hospital.is_active else 'désactivé'}",
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    messages.success(request, f"Hôpital {'activé' if hospital.is_active else 'désactivé'} avec succès")
    return redirect('admin_hospitals_list')


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_hospital_verify(request, hospital_id):
    """Vérifier un hôpital"""
    hospital = get_object_or_404(Hospital, id=hospital_id)
    hospital.verified_at = timezone.now()
    hospital.verified_by = request.user
    hospital.is_active = True
    hospital.save()
    
    # Créer un log
    SystemLog.objects.create(
        user=request.user,
        action_type='hospital_verify',
        description=f"Hôpital {hospital.name} vérifié",
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    messages.success(request, f"Hôpital {hospital.name} vérifié avec succès")
    return redirect('admin_hospitals_list')


# ========================================================
# VUES POUR MÉDECINS
# ========================================================

@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_doctors_list(request):
    """Liste des médecins"""
    doctors = Doctor.objects.select_related('speciality', 'hospital').all()
    
    context = {
        'doctors': doctors,
    }
    return render(request, 'mapli/admin/doctors_list.html', context)


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_doctor_detail(request, doctor_id):
    """Détail d'un médecin"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    return render(request, 'mapli/admin/doctor_detail.html', {'doctor': doctor})


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_doctor_toggle(request, doctor_id):
    """Activer/désactiver un médecin"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    doctor.is_active = not doctor.is_active
    doctor.save()
    
    # Créer un log
    SystemLog.objects.create(
        user=request.user,
        action_type='doctor_toggle',
        description=f"Médecin Dr. {doctor.name} {'activé' if doctor.is_active else 'désactivé'}",
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    messages.success(request, f"Médecin {'activé' if doctor.is_active else 'désactivé'} avec succès")
    return redirect('admin_doctors_list')


@login_required
@role_required(UserRoles.ADMIN_SYSTEME)
def admin_doctor_verify(request, doctor_id):
    """Vérifier un médecin"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    doctor.verified_at = timezone.now()
    doctor.verified_by = request.user
    doctor.is_active = True
    doctor.save()
    
    # Créer un log
    SystemLog.objects.create(
        user=request.user,
        action_type='doctor_verify',
        description=f"Médecin Dr. {doctor.name} vérifié",
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    messages.success(request, f"Médecin Dr. {doctor.name} vérifié avec succès")
    return redirect('admin_doctors_list')