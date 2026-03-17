from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    CustomUser, Fonctionnalite, SystemLog,
    PregnancyCalendar, PregnancyMilestone, PregnancySymptom, PregnancyChecklist,
    UserProfile, HospitalProfile, DoctorProfile,
    Speciality, Hospital, Doctor, Patient,
    Pregnancy, Appointment, PregnancyAppointment
)

# ============================================
# ADMIN POUR CustomUser (avec rôles)
# ============================================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_approved', 'is_active')  # user_type → role
    list_filter = ('role', 'is_approved', 'is_active', 'is_staff')  # user_type → role
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'date_of_birth', 'phone_number')
        }),
        ('Localisation', {
            'fields': ('country', 'province', 'commune', 'district')
        }),
        ('Rôle et statut', {
            'fields': ('role', 'is_approved', 'is_active', 'is_staff', 'is_superuser')  # user_type → role
        }),
        ('Grossesse', {
            'fields': ('is_pregnant', 'current_pregnancy_week', 'last_menstrual_period', 'blood_type', 'allergies'),
            'classes': ('collapse',),
        }),
        ('Fonctionnalités autorisées', {
            'fields': ('authorized_features',),
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined', 'last_profile_update'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role'),  # user_type → role
        }),
    )

# ============================================
# ADMIN POUR Fonctionnalite
# ============================================
@admin.register(Fonctionnalite)
class FonctionnaliteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'categorie', 'est_active_globalement', 'date_creation')
    list_filter = ('categorie', 'est_active_globalement')
    search_fields = ('nom', 'code', 'description')
    ordering = ('categorie', 'nom')

# ============================================
# ADMIN POUR SystemLog
# ============================================
@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'user', 'created_at', 'ip_address')
    list_filter = ('action_type', 'created_at')
    search_fields = ('description', 'user__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

# ============================================
# ADMIN POUR PregnancyCalendar
# ============================================
class PregnancyMilestoneInline(admin.TabularInline):
    model = PregnancyMilestone
    extra = 1

@admin.register(PregnancyCalendar)
class PregnancyCalendarAdmin(admin.ModelAdmin):
    list_display = ('user', 'week_number', 'trimester', 'is_current', 'is_completed')
    list_filter = ('trimester', 'is_current', 'is_completed')
    search_fields = ('user__email', 'user__username')
    inlines = [PregnancyMilestoneInline]
    fieldsets = (
        ('Informations générales', {
            'fields': ('user', 'week_number', 'trimester', 'is_current', 'is_completed')
        }),
        ('Développement', {
            'fields': ('baby_size', 'baby_weight', 'baby_development', 'mother_changes')
        }),
        ('Conseils', {
            'fields': ('nutrition_tips', 'medical_advice', 'exercises', 'recommended_appointments')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
    )

@admin.register(PregnancyMilestone)
class PregnancyMilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'calendar', 'week_number', 'is_completed')
    list_filter = ('is_completed', 'week_number')
    search_fields = ('title', 'description')

@admin.register(PregnancySymptom)
class PregnancySymptomAdmin(admin.ModelAdmin):
    list_display = ('user', 'symptom_type', 'week_number', 'severity', 'date')
    list_filter = ('symptom_type', 'severity', 'date')
    search_fields = ('user__username', 'description')

@admin.register(PregnancyChecklist)
class PregnancyChecklistAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'week_number', 'category', 'is_done')
    list_filter = ('is_done', 'category', 'week_number')
    search_fields = ('task', 'user__username')

# ============================================
# ADMIN POUR UserProfile
# ============================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'emergency_contact_name', 'preferred_hospital')
    search_fields = ('user__username', 'emergency_contact_name')

# ============================================
# ADMIN POUR HospitalProfile
# ============================================
@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'hospital', 'registration_number', 'approved_by', 'approved_at')
    list_filter = ('approved_at',)
    search_fields = ('user__username', 'hospital__name', 'registration_number')
    readonly_fields = ('approved_at',)

# ============================================
# ADMIN POUR DoctorProfile
# ============================================
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor', 'license_number', 'consultation_fee', 'approved_by')
    list_filter = ('approved_at',)
    search_fields = ('user__username', 'doctor__name', 'license_number')

# ============================================
# ADMIN POUR Speciality
# ============================================
@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# ============================================
# ADMIN POUR Hospital
# ============================================
@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'has_ultrasound', 'has_maternity', 'is_active')
    list_filter = ('has_ultrasound', 'has_maternity', 'is_active')
    search_fields = ('name', 'address', 'email')
    readonly_fields = ('verified_at',)

# ============================================
# ADMIN POUR Doctor
# ============================================
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'speciality', 'hospital', 'is_available', 'is_active')
    list_filter = ('speciality', 'hospital', 'is_available', 'is_active')
    search_fields = ('name', 'email', 'phone_number')
    readonly_fields = ('verified_at',)

# ============================================
# ADMIN POUR Patient
# ============================================
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'medical_record_number', 'registered_at')
    list_filter = ('registered_at',)
    search_fields = ('name', 'email', 'phone_number', 'medical_record_number')
    readonly_fields = ('medical_record_number', 'registered_at')
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('user', 'name', 'date_of_birth', 'nationality')
        }),
        ('Contact', {
            'fields': ('email', 'phone_number', 'address')
        }),
        ('Localisation', {
            'fields': ('country', 'province', 'commune', 'current_district', 'latitude', 'longitude')
        }),
        ('Médical', {
            'fields': ('blood_type', 'allergies')
        }),
        ('Enregistrement', {
            'fields': ('medical_record_number', 'registered_by', 'registered_at')
        }),
    )

# ============================================
# ADMIN POUR Pregnancy
# ============================================
@admin.register(Pregnancy)
class PregnancyAdmin(admin.ModelAdmin):
    list_display = ('patient', 'start_date', 'estimated_delivery_date', 'current_trimester', 'is_active')
    list_filter = ('current_trimester', 'is_active')
    search_fields = ('patient__name',)

# ============================================
# ADMIN POUR Appointment
# ============================================
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'doctor', 'hospital', 'scheduled_date', 'status', 'is_confirmed')
    list_filter = ('status', 'is_confirmed', 'hospital', 'scheduled_date')
    search_fields = ('patient_name', 'patient_email', 'doctor__name')
    readonly_fields = ('registration_number', 'created_at')
    fieldsets = (
        ('Patient', {
            'fields': ('user', 'patient_name', 'patient_email', 'patient_phone')
        }),
        ('Rendez-vous', {
            'fields': ('doctor', 'hospital', 'scheduled_date', 'appointment_date', 'daily_sequence', 'status')
        }),
        ('Détails', {
            'fields': ('reason', 'ultrasound_type', 'pregnancy_week', 'price')
        }),
        ('Suivi', {
            'fields': ('is_confirmed', 'receipt_sent', 'created_by', 'created_at')
        }),
    )

# ============================================
# ADMIN POUR PregnancyAppointment
# ============================================
@admin.register(PregnancyAppointment)
class PregnancyAppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'appointment_type', 'trimester', 'scheduled_date', 'status')
    list_filter = ('appointment_type', 'trimester', 'status')
    search_fields = ('patient_name', 'doctor__name')
    fieldsets = (
        ('Patient', {
            'fields': ('patient_name', 'patient_email', 'patient_phone')
        }),
        ('Rendez-vous', {
            'fields': ('doctor', 'hospital', 'scheduled_date', 'appointment_type', 'trimester', 'status')
        }),
        ('Détails médicaux', {
            'fields': ('reason', 'is_anomaly_detected', 'notes')
        }),
    )