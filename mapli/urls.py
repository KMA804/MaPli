# mapli/urls.py
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

# Import des vues (organisées par catégorie)
from .views import register_views, admin_views

# Vues principales
from .views.home import home, about, services, doctors, departments, appointment_view, pregnancy_ultrasound_request
from .views.aposucces import appointment_success, download_receipt
from .views.apiuser import get_user_profile
from .views.authentification import register_view, login_view, logout_view, dashboard_view
from .views.periode import validation_periode, exercices_adaptes
from .views.pregnancy_calendar import (
    pregnancy_calendar_view,
    update_pregnancy_week_ajax,
    week_detail_view,
    add_symptom_view,
    toggle_task_view
)
from .views.appointments_list import my_appointments_view
from .views.profile import profile_view
from .views.faq import faq_view

# ViewSets API
from .views.appointment import (
    HospitalViewSet,
    SpecialityViewSet, 
    DoctorViewSet, 
    PatientViewSet, 
    PregnancyViewSet, 
    AppointmentViewSet,
    PregnancyAppointmentViewSet
)


# ========================================================
# CONFIGURATION DU ROUTEUR DRF
# ========================================================
router = DefaultRouter()
router.register(r'hospitals', HospitalViewSet)
router.register(r'specialities', SpecialityViewSet)
router.register(r'doctors', DoctorViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'pregnancies', PregnancyViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'pregnancy-appointments', PregnancyAppointmentViewSet)


# ========================================================
# URLS PRINCIPALES (organisées par fonctionnalité)
# ========================================================
urlpatterns = [

    # --------------------------------------------------------
    # 1. AUTHENTIFICATION (publiques)
    # --------------------------------------------------------
    path('', login_view, name='index'),
    path('index/', login_view, name='index'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Inscriptions par rôle
    path('register/patient/', register_views.register_patient, name='register_patient'),
    path('register/hospital/', register_views.register_hospital, name='register_hospital'),
    path('register/doctor/', register_views.register_doctor, name='register_doctor'),
    
    # Réinitialisation mot de passe
    path('password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='mapli/password_reset.html',
            email_template_name='mapli/password_reset_email.html',
            subject_template_name='mapli/password_reset_subject.txt',
            success_url='/password-reset/done/'
        ), 
        name='password_reset'),
    path('password-reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='mapli/password_reset_done.html'
        ), 
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='mapli/password_reset_confirm.html',
            success_url='/password-reset-complete/'
        ), 
        name='password_reset_confirm'),
    path('password-reset-complete/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='mapli/password_reset_complete.html'
        ), 
        name='password_reset_complete'),

    # --------------------------------------------------------
    # 2. ADMINISTRATION SYSTÈME (A)
    # --------------------------------------------------------

    # Dashboard
    path('gestion/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),

    # Gestion des utilisateurs
    path('gestion/users/', admin_views.admin_users_list, name='admin_users_list'),
    path('gestion/users/<int:user_id>/', admin_views.admin_user_detail, name='admin_user_detail'),
    path('gestion/users/<int:user_id>/toggle/', admin_views.admin_user_toggle, name='admin_user_toggle'),

    # Gestion des patients (remplace clients)
    path('gestion/patients/', admin_views.admin_patients_list, name='admin_patients_list'),
    path('gestion/patients/<int:patient_id>/', admin_views.admin_patient_detail, name='admin_patient_detail'),
    path('gestion/patients/<int:patient_id>/toggle/', admin_views.admin_patient_toggle, name='admin_patient_toggle'),
    path('gestion/patients/<int:patient_id>/features/', admin_views.admin_patient_features, name='admin_patient_features'),

    # Gestion des fonctionnalités
    path('gestion/features/', admin_views.admin_features_list, name='admin_features_list'),
    path('gestion/features/add/', admin_views.admin_add_feature, name='admin_add_feature'),
    path('gestion/features/<int:feature_id>/toggle/', admin_views.admin_feature_toggle, name='admin_feature_toggle'),
    path('gestion/features/<int:feature_id>/access/', admin_views.admin_feature_access, name='admin_feature_access'),

    # Gestion des hôpitaux
    path('gestion/hospitals/', admin_views.admin_hospitals_list, name='admin_hospitals_list'),
    path('gestion/hospitals/<int:hospital_id>/', admin_views.admin_hospital_detail, name='admin_hospital_detail'),
    path('gestion/hospitals/<int:hospital_id>/toggle/', admin_views.admin_hospital_toggle, name='admin_hospital_toggle'),
    path('gestion/hospitals/<int:hospital_id>/verify/', admin_views.admin_hospital_verify, name='admin_hospital_verify'),

    # Gestion des médecins
    path('gestion/doctors/', admin_views.admin_doctors_list, name='admin_doctors_list'),
    path('gestion/doctors/<int:doctor_id>/', admin_views.admin_doctor_detail, name='admin_doctor_detail'),
    path('gestion/doctors/<int:doctor_id>/toggle/', admin_views.admin_doctor_toggle, name='admin_doctor_toggle'),
    path('gestion/doctors/<int:doctor_id>/verify/', admin_views.admin_doctor_verify, name='admin_doctor_verify'),

    # Gestion des logs
    path('gestion/logs/', admin_views.admin_logs_list, name='admin_logs'),
    path('gestion/logs/<int:log_id>/', admin_views.admin_log_detail, name='admin_log_detail'),

    # --------------------------------------------------------
    # 3. PAGES PUBLIQUES / INFORMATIVES
    # --------------------------------------------------------
    path('home/', login_required(home), name='home'),
    path('about/', login_required(about), name='about'),
    path('services/', login_required(services), name='services'),
    path('doctors/', login_required(doctors), name='doctors'),
    path('departments/', login_required(departments), name='departments'),
    path('faq/', faq_view, name='faq'),
    path('contact/', login_required(TemplateView.as_view(template_name='mapli/contact.html')), name='contact'),
    path('testimonials/', login_required(TemplateView.as_view(template_name='mapli/testimonials.html')), name='testimonials'),
    path('gallery/', login_required(TemplateView.as_view(template_name='mapli/gallery.html')), name='gallery'),
    
    # Pages de détails
    path('department-details/', login_required(TemplateView.as_view(template_name='mapli/department_details.html')), name='department_details'),
    path('service-details/', login_required(TemplateView.as_view(template_name='mapli/service_details.html')), name='service_details'),
    
    # Pages légales
    path('terms/', login_required(TemplateView.as_view(template_name='mapli/terms.html')), name='terms'),
    path('privacy/', login_required(TemplateView.as_view(template_name='mapli/privacy.html')), name='privacy'),

    # --------------------------------------------------------
    # 4. GESTION DES RENDEZ-VOUS
    # --------------------------------------------------------
    path('appointment/', login_required(appointment_view), name='appoint'),
    path('pregnancy-ultrasound/', login_required(pregnancy_ultrasound_request), name='pregnancy_ultrasound'),
    path('my-appointments/', login_required(my_appointments_view), name='my_appointments'),
    
    # Confirmation et reçus
    path('appointment/success/<int:appointment_id>/', login_required(appointment_success), name='appointment_success'),
    path('appointment/receipt/<int:appointment_id>/', login_required(download_receipt), name='download_receipt'),

    # --------------------------------------------------------
    # 5. CALENDRIER DE GROSSESSE
    # --------------------------------------------------------
    path('pregnancy/calendar/', login_required(pregnancy_calendar_view), name='pregnancy_calendar'),
    path('pregnancy/update-week/', login_required(update_pregnancy_week_ajax), name='update_pregnancy_week_ajax'),
    path('pregnancy/week/<int:week_number>/', login_required(week_detail_view), name='week_detail'),
    path('pregnancy/add-symptom/', login_required(add_symptom_view), name='add_symptom'),
    path('pregnancy/task/<int:task_id>/toggle/', login_required(toggle_task_view), name='toggle_task'),

    # --------------------------------------------------------
    # 6. EXERCICES ET PÉRIODES
    # --------------------------------------------------------
    path('exercices/validation-periode/', validation_periode, name='validation_periode'),
    path('exercices/adaptes/', exercices_adaptes, name='exercices_adaptes'),

    # --------------------------------------------------------
    # 7. PROFIL UTILISATEUR
    # --------------------------------------------------------
    path('profile/', login_required(profile_view), name='profile'),
    path('api/user/profile/', get_user_profile, name='user-profile'),

    # --------------------------------------------------------
    # 8. API REST
    # --------------------------------------------------------
    # Endpoints API spécifiques
    path('api/appointments/available_time_slots/', 
        AppointmentViewSet.as_view({'get': 'available_time_slots'}), 
        name='appointment-available-time-slots'),
    
    path('api/appointments/hospital_capacity/', 
        AppointmentViewSet.as_view({'get': 'hospital_capacity'}), 
        name='appointment-hospital-capacity'),
    
    path('api/appointments/<int:pk>/download-receipt/', 
        AppointmentViewSet.as_view({'get': 'download_receipt'}), 
        name='appointment-download-receipt'),
    
    path('api/appointments/<int:pk>/confirm-payment/', 
        AppointmentViewSet.as_view({'post': 'confirm_payment'}), 
        name='appointment-confirm-payment'),
    
    path('api/appointments/create_public_appointment/', 
        AppointmentViewSet.as_view({'post': 'create_public_appointment'}), 
        name='appointment-create-public'),
    
    path('api/appointments/available_slots/', 
        AppointmentViewSet.as_view({'get': 'available_slots'}), 
        name='appointment-available-slots'),
    
    # Inclusion du router DRF
    path('api/', include(router.urls)),
]