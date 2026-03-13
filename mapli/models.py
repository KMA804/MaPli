# models.py (extrait à ajouter/modifier)

from django.db import models
import uuid
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Définir les choix de rôles
class UserRoles:
    ADMIN_SYSTEME = 'admin_systeme'  # A - Administrateur système
    HOPITAL = 'hopital'              # Hôpital
    MEDECIN = 'medecin'              # Médecin
    PATIENT = 'patient'               # Patient (B)
    
    CHOICES = [
        (ADMIN_SYSTEME, 'Administrateur système'),
        (HOPITAL, 'Hôpital'),
        (MEDECIN, 'Médecin'),
        (PATIENT, 'Patient'),
    ]

# D'abord définir CustomUser
class CustomUser(AbstractUser):
    # Champs existants
    date_of_birth = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date de naissance"
    )
    
    # AJOUTEZ CE CHAMP PROVINCE
    province = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Province"
    )
    
    # Vos autres champs existants
    country = models.CharField(
        max_length=100, 
        default='République Démocratique du Congo'
    )
    commune = models.CharField(max_length=100, blank=True)
    district = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Colline ou quartier"
    )
    job_title = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Poste de travail"
    )
    
    # Champs liés à la grossesse
    is_pregnant = models.BooleanField(default=False)
    current_pregnancy_week = models.IntegerField(null=True, blank=True)
    last_menstrual_period = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    last_profile_update = models.DateTimeField(auto_now=True)
    
    # Champs de contact
    phone_number = models.CharField(max_length=20, blank=True)
    
    # NOUVEAU: Champ rôle
    role = models.CharField(
        max_length=20,
        choices=UserRoles.CHOICES,
        default=UserRoles.PATIENT,
        verbose_name="Rôle utilisateur"
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_full_address(self):
        """Retourne l'adresse complète"""
        return f"{self.district}, {self.commune}, {self.province}, {self.country}"
    
    # NOUVEAU: Statut du compte
    is_approved = models.BooleanField(
        default=False,
        help_text="Compte approuvé par l'administrateur système"
    )
    
    # NOUVEAU: Fonctionnalités autorisées (pour les patients)
    authorized_features = models.ManyToManyField(
        'Fonctionnalite',
        blank=True,
        help_text="Fonctionnalités accessibles (pour les patients)"
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_role_display_name(self):
        """Retourne le nom du rôle en français"""
        return dict(UserRoles.CHOICES).get(self.role, self.role)
    def save(self, *args, **kwargs):
        # Si c'est un superuser et que le rôle n'est pas défini, mettre admin_systeme
        if self.is_superuser and not self.role:
            self.role = UserRoles.ADMIN_SYSTEME
        super().save(*args, **kwargs)
    def is_admin_systeme(self):
        return self.role == UserRoles.ADMIN_SYSTEME
    
    def is_hopital(self):
        return self.role == UserRoles.HOPITAL
    
    def is_medecin(self):
        return self.role == UserRoles.MEDECIN
    
    def is_patient(self):
        return self.role == UserRoles.PATIENT

# NOUVEAU: Modèle pour les fonctionnalités système
class Fonctionnalite(models.Model):
    """Fonctionnalités que l'admin système peut activer/désactiver"""
    
    CATEGORIE_CHOICES = [
        ('rendez_vous', 'Rendez-vous'),
        ('calendrier', 'Calendrier grossesse'),
        ('documents', 'Documents médicaux'),
        ('paiement', 'Paiement en ligne'),
        ('messagerie', 'Messagerie'),
        ('statistiques', 'Statistiques'),
    ]
    
    nom = models.CharField(max_length=100, verbose_name="Nom de la fonctionnalité")
    code = models.CharField(max_length=50, unique=True, verbose_name="Code unique")
    description = models.TextField(blank=True, verbose_name="Description")
    categorie = models.CharField(max_length=50, choices=CATEGORIE_CHOICES, default='rendez_vous')
    est_active_globalement = models.BooleanField(default=True, verbose_name="Active globalement")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    # Rôles qui peuvent utiliser cette fonctionnalité par défaut
    roles_autorises = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des rôles autorisés par défaut"
    )
    
    class Meta:
        verbose_name = "Fonctionnalité"
        verbose_name_plural = "Fonctionnalités"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    def is_accessible_by(self, user):
        """Vérifie si un utilisateur peut accéder à cette fonctionnalité"""
        if user.is_admin_systeme():
            return True
        if not self.est_active_globalement:
            return False
        if user.is_patient():
            return self in user.authorized_features.all()
        # Pour les autres rôles (hopital, medecin), vérifier si leur rôle est dans roles_autorises
        return user.role in self.roles_autorises

# NOUVEAU: Modèle pour les journaux d'activité
class SystemLog(models.Model):
    """Journalisation des actions système"""
    
    ACTION_TYPES = [
        ('user_create', 'Création utilisateur'),
        ('user_update', 'Modification utilisateur'),
        ('user_delete', 'Suppression utilisateur'),
        ('feature_toggle', 'Activation/désactivation fonctionnalité'),
        ('permission_change', 'Changement permission'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('system', 'Système'),
    ]
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='system_logs'
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Journal système"
        verbose_name_plural = "Journaux système"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.created_at}"

# MAINTENANT définir les modèles du calendrier de grossesse
class PregnancyCalendar(models.Model):
    """Calendrier de grossesse pour suivre l'évolution semaine par semaine"""
    
    TRIMESTER_CHOICES = [
        (1, 'Premier trimestre'),
        (2, 'Deuxième trimestre'),
        (3, 'Troisième trimestre'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pregnancy_calendars')
    week_number = models.PositiveIntegerField(verbose_name="Numéro de semaine")
    trimester = models.PositiveIntegerField(choices=TRIMESTER_CHOICES, verbose_name="Trimestre")
    
    # Informations sur la semaine
    baby_size = models.CharField(max_length=100, blank=True, verbose_name="Taille du bébé")
    baby_weight = models.CharField(max_length=100, blank=True, verbose_name="Poids du bébé")
    baby_development = models.TextField(blank=True, verbose_name="Développement du bébé")
    mother_changes = models.TextField(blank=True, verbose_name="Changements chez la mère")
    
    # Conseils et recommandations
    nutrition_tips = models.TextField(blank=True, verbose_name="Conseils nutritionnels")
    medical_advice = models.TextField(blank=True, verbose_name="Conseils médicaux")
    exercises = models.TextField(blank=True, verbose_name="Exercices recommandés")
    
    # Rendez-vous recommandés
    recommended_appointments = models.TextField(blank=True, verbose_name="Rendez-vous recommandés")
    
    # État de la semaine pour l'utilisatrice
    is_completed = models.BooleanField(default=False, verbose_name="Semaine complétée")
    is_current = models.BooleanField(default=False, verbose_name="Semaine en cours")
    notes = models.TextField(blank=True, verbose_name="Notes personnelles")
    
    # Dates
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début de la semaine")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin de la semaine")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Calendrier de grossesse"
        verbose_name_plural = "Calendriers de grossesse"
        unique_together = ['user', 'week_number']
        ordering = ['week_number']
    
    def __str__(self):
        return f"Semaine {self.week_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        # Définir automatiquement le trimestre en fonction de la semaine
        if self.week_number <= 13:
            self.trimester = 1
        elif self.week_number <= 26:
            self.trimester = 2
        else:
            self.trimester = 3
        super().save(*args, **kwargs)


class PregnancyMilestone(models.Model):
    """Étapes importantes de la grossesse"""
    
    calendar = models.ForeignKey(PregnancyCalendar, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    week_number = models.PositiveIntegerField(verbose_name="Semaine concernée")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Icône")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Étape importante"
        verbose_name_plural = "Étapes importantes"
        ordering = ['week_number']
    
    def __str__(self):
        return f"{self.title} - Semaine {self.week_number}"


class PregnancySymptom(models.Model):
    """Suivi des symptômes par semaine"""
    
    SYMPTOM_TYPES = [
        ('nausea', 'Nausées'),
        ('fatigue', 'Fatigue'),
        ('back_pain', 'Maux de dos'),
        ('headache', 'Maux de tête'),
        ('swelling', 'Gonflements'),
        ('cravings', 'Envie alimentaire'),
        ('other', 'Autre'),
    ]
    
    SEVERITY_CHOICES = [
        (1, 'Léger'),
        (2, 'Modéré'),
        (3, 'Intense'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pregnancy_symptoms')
    week_number = models.PositiveIntegerField(verbose_name="Semaine")
    symptom_type = models.CharField(max_length=50, choices=SYMPTOM_TYPES)
    severity = models.PositiveIntegerField(choices=SEVERITY_CHOICES, default=1)
    description = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Symptôme"
        verbose_name_plural = "Symptômes"
        ordering = ['-date']


class PregnancyChecklist(models.Model):
    """Checklist des choses à faire pendant la grossesse"""
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pregnancy_checklists')
    week_number = models.PositiveIntegerField(verbose_name="Semaine")
    task = models.CharField(max_length=300, verbose_name="Tâche")
    category = models.CharField(max_length=100, verbose_name="Catégorie")
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)
    reminder_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Tâche à faire"
        verbose_name_plural = "Tâches à faire"
        ordering = ['week_number', 'category']
    
    def __str__(self):
        return f"Semaine {self.week_number}: {self.task}"

# MODIFICATION: UserProfile simplifié car les rôles sont dans CustomUser
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    preferred_hospital = models.ForeignKey('Hospital', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile de {self.user.get_full_name()}"

# NOUVEAU: Profil pour les hôpitaux
class HospitalProfile(models.Model):
    """Informations supplémentaires pour les comptes hôpital"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='hospital_profile')
    hospital = models.OneToOneField('Hospital', on_delete=models.CASCADE, related_name='user_account')
    registration_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro d'agrément")
    director_name = models.CharField(max_length=200)
    director_phone = models.CharField(max_length=20)
    license_document = models.FileField(upload_to='hospital_licenses/', null=True, blank=True)
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_hospitals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Profil hôpital: {self.hospital.name}"

# NOUVEAU: Profil pour les médecins
class DoctorProfile(models.Model):
    """Informations supplémentaires pour les comptes médecin"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor_profile')
    doctor = models.OneToOneField('Doctor', on_delete=models.CASCADE, related_name='user_account')
    license_number = models.CharField(max_length=50, verbose_name="Numéro d'ordre")
    specialization_certificate = models.FileField(upload_to='doctor_certificates/', null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_doctors'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Profil médecin: Dr. {self.doctor.name}"

class Speciality(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    has_ultrasound = models.BooleanField(default=False)
    has_maternity = models.BooleanField(default=False)
    services = models.TextField(blank=True)
    
    # NOUVEAU: Statut de l'hôpital
    is_active = models.BooleanField(default=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_hospitals'
    )
    
    def __str__(self):
        return self.name

class Doctor(models.Model):
    name = models.CharField(max_length=200)
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name='doctors')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='doctors')
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    is_available = models.BooleanField(default=True)
    
    # NOUVEAU: Statut du médecin
    is_active = models.BooleanField(default=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_doctors'
    )

    def __str__(self):
        return f"Dr. {self.name} - {self.speciality.name}"

# MODIFICATION: Patient lié à CustomUser
class Patient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile', null=True, blank=True)
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='République Démocratique du Congo')
    province = models.CharField(max_length=100)
    commune = models.CharField(max_length=100)
    current_district = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    blood_type = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # NOUVEAU: Numéro de dossier
    medical_record_number = models.CharField(max_length=50, unique=True, blank=True)
    registered_at = models.DateTimeField(
        auto_now_add=True,
        null=True,  # ← AJOUTEZ CECI
        blank=True  # ← ET CECI (optionnel)
    )
    registered_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='registered_patients'
    )

    def save(self, *args, **kwargs):
        if not self.medical_record_number:
            # Générer un numéro de dossier unique
            year = timezone.now().year
            last_patient = Patient.objects.filter(
                medical_record_number__startswith=f"PAT-{year}"
            ).order_by('medical_record_number').last()
            if last_patient:
                last_num = int(last_patient.medical_record_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.medical_record_number = f"PAT-{year}-{new_num:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_full_address(self):
        """Retourne l'adresse complète pour la géolocalisation"""
        return f"{self.current_district}, {self.commune}, {self.province}, {self.country}"

class Pregnancy(models.Model):
    TRIMESTER_CHOICES = [
        (1, 'Premier trimestre (1-3 mois)'),
        (2, 'Deuxième trimestre (4-6 mois)'),
        (3, 'Troisième trimestre (7-9 mois)'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pregnancies')
    start_date = models.DateField(help_text="Date des dernières règles (DDR)")
    estimated_delivery_date = models.DateField(blank=True, null=True)
    current_trimester = models.IntegerField(choices=TRIMESTER_CHOICES, default=1)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.start_date and not self.estimated_delivery_date:
            self.estimated_delivery_date = self.start_date + timedelta(weeks=40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Grossesse de {self.patient.name}"

class PatientSession(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    selected_hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PE', 'En attente'
        CONFIRMED = 'CO', 'Confirmé'
        COMPLETED = 'CM', 'Terminé'
        CANCELLED = 'CA', 'Annulé'
        NO_SHOW = 'NS', 'Patient absent'

    # Champs existants
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    patient_name = models.CharField(max_length=200)
    patient_email = models.EmailField()
    patient_phone = models.CharField(max_length=20)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='appointments')
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.PENDING)
    reason = models.TextField(help_text="Raison de la consultation")
    ultrasound_type = models.CharField(max_length=100, blank=True)
    pregnancy_week = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    registration_number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Nouveaux champs
    appointment_date = models.DateField(null=True, blank=True, help_text="Date réelle du rendez-vous")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Prix de l'échographie en FCFA")
    daily_sequence = models.IntegerField(default=0, help_text="Numéro dans la file d'attente (1-20)")
    is_confirmed = models.BooleanField(default=True, help_text="Rendez-vous confirmé")
    receipt_sent = models.BooleanField(default=False, help_text="Reçu envoyé par email")
    
    # NOUVEAU: Champ pour l'utilisateur qui a créé le rendez-vous
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_appointments'
    )

    class Meta:
        unique_together = ['doctor', 'scheduled_date']

    def __str__(self):
        return f"RDV le {self.scheduled_date} - {self.patient_name}"
    
    def clean(self):
        """Validation des contraintes horaires"""
        from django.core.exceptions import ValidationError
        from datetime import time
        
        if self.scheduled_date:
            # Vérification jour de semaine (lundi=0, dimanche=6)
            if self.scheduled_date.weekday() >= 5:  # Samedi (5) ou Dimanche (6)
                raise ValidationError("Les rendez-vous ne sont pas disponibles le week-end.")
            
            # Vérification heures de travail
            appointment_time = self.scheduled_date.time()
            morning_start = time(7, 0)
            morning_end = time(12, 0)
            afternoon_start = time(14, 0)
            afternoon_end = time(17, 0)
            
            if not ((morning_start <= appointment_time <= morning_end) or 
                   (afternoon_start <= appointment_time <= afternoon_end)):
                raise ValidationError("Les rendez-vous sont disponibles de 7h-12h et 14h-17h uniquement.")
    
    def save(self, *args, **kwargs):
        """Surcharge UNIFIÉE de la méthode save pour calcul automatique ET validation"""
        # Calculs automatiques AVANT la validation
        if not self.appointment_date:
            self.calculate_appointment_date()
        if self.price == 0:
            self.calculate_price()
        
        # Validation complète
        self.full_clean()
        
        # Sauvegarde
        super().save(*args, **kwargs)
    
    def calculate_appointment_date(self):
        """Calcule la date réelle du rendez-vous - VERSION OPTIMISÉE"""
        from datetime import timedelta
        from django.db.models import Count
        
        hospital_capacity = 20
        
        # Si scheduled_date est un datetime, on prend la date seulement
        requested_date = self.scheduled_date.date() if hasattr(self.scheduled_date, 'date') else self.scheduled_date
        
        # OPTIMISATION: Vérifier d'abord la date demandée
        same_day_count = Appointment.objects.filter(
            hospital=self.hospital,
            appointment_date=requested_date,
            is_confirmed=True
        ).count()
        
        if same_day_count < hospital_capacity:
            self.appointment_date = requested_date
            self.daily_sequence = same_day_count + 1
            return  # Sortie rapide
        
        # OPTIMISATION: Limiter la recherche à 30 jours max
        max_days_check = 30
        current_date = requested_date + timedelta(days=1)
        days_checked = 0
        
        while days_checked < max_days_check:
            appointments_count = Appointment.objects.filter(
                hospital=self.hospital,
                appointment_date=current_date,
                is_confirmed=True
            ).count()
            
            if appointments_count < hospital_capacity:
                self.appointment_date = current_date
                self.daily_sequence = appointments_count + 1
                return  # Sortie rapide
                
            current_date += timedelta(days=1)
            days_checked += 1
        
        # Fallback: utiliser la date demandée même si complète
        self.appointment_date = requested_date
        self.daily_sequence = hospital_capacity
    
    def calculate_price(self):
        """Calcule le prix selon le type d'échographie"""
        price_mapping = {
            'DATING': 50000,           # 50,000 FBu
            'FIRST_TRIMESTER': 60000,  # 60,000 FBu  
            'SECOND_TRIMESTER': 75000, # 75,000 FBu
            'THIRD_TRIMESTER': 60000,  # 60,000 FBu
            'SPECIALIZED': 100000,     # 100,000 FBu
        }
        self.price = price_mapping.get(self.ultrasound_type, 50000)
    
    def get_formatted_price(self):
        """Retourne le prix formaté"""
        return f"{self.price:,.0f} FBu".replace(",", " ") 

class PregnancyAppointment(Appointment):
    APPOINTMENT_TYPES = (
        ('PRENATAL', 'Consultation prénatale'),
        ('ULTRASOUND', 'Échographie'),
        ('LABOR', 'Consultation de travail'),
        ('POSTNATAL', 'Consultation postnatale'),
    )
    TRIMESTER = (
        (1, 'Premier trimestre'),
        (2, 'Deuxième trimestre'),
        (3, 'Troisième trimestre'),
    )

    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES)
    trimester = models.IntegerField(choices=TRIMESTER, blank=True, null=True)
    is_anomaly_detected = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_appointment_type_display()} - {self.patient_name}"