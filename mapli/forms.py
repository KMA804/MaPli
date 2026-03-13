# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Hospital, Doctor, HospitalProfile, DoctorProfile, UserRoles


# ========================================================
# FORMULAIRES D'AUTHENTIFICATION
# ========================================================

class CustomUserCreationForm(UserCreationForm):
    """Formulaire d'inscription pour les patients"""
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'date_of_birth', 'phone_number', 'country', 'province', 
            'commune', 'district', 'job_title', 'is_pregnant', 
            'current_pregnancy_week', 'last_menstrual_period', 
            'blood_type', 'allergies'
        ]
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRoles.PATIENT
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Formulaire de connexion"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom d'utilisateur ou email",
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Nom d'utilisateur ou mot de passe incorrect.")
        return cleaned_data


# ========================================================
# FORMULAIRES D'INSCRIPTION SPÉCIFIQUES
# ========================================================

class PatientRegistrationForm(CustomUserCreationForm):
    """Alias pour CustomUserCreationForm"""
    pass


class HospitalRegistrationForm(UserCreationForm):
    """Inscription pour les hôpitaux"""
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRoles.HOPITAL
        user.is_active = False  # Nécessite approbation admin
        if commit:
            user.save()
        return user


class HospitalInfoForm(forms.ModelForm):
    """Informations de l'hôpital"""
    class Meta:
        model = Hospital
        fields = ['name', 'phone_number', 'email', 'address', 'has_ultrasound', 'has_maternity']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class HospitalProfileForm(forms.ModelForm):
    """Profil détaillé de l'hôpital"""
    class Meta:
        model = HospitalProfile
        fields = ['registration_number', 'director_name', 'director_phone', 'license_document']


class DoctorRegistrationForm(UserCreationForm):
    """Inscription pour les médecins"""
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRoles.MEDECIN
        user.is_active = False  # Nécessite approbation admin
        if commit:
            user.save()
        return user


class DoctorInfoForm(forms.ModelForm):
    """Informations du médecin"""
    class Meta:
        model = Doctor
        fields = ['name', 'speciality', 'hospital', 'phone_number', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = "Nom complet"
        # Ne montrer que les hôpitaux approuvés
        self.fields['hospital'].queryset = Hospital.objects.filter(is_active=True)


class DoctorProfileForm(forms.ModelForm):
    """Profil détaillé du médecin"""
    class Meta:
        model = DoctorProfile
        fields = ['license_number', 'specialization_certificate', 'consultation_fee']


# ========================================================
# FORMULAIRES POUR LES FONCTIONNALITÉS SPÉCIFIQUES
# ========================================================

class PeriodeGrossesseForm(forms.Form):
    """
    Formulaire pour calculer la période de grossesse
    Utilisé dans la vue validation_periode
    """
    CHOIX_METHODE = [
        ('ddr', 'Date des dernières règles'),
        ('semaines', 'Semaines de grossesse'),
    ]
    
    methode = forms.ChoiceField(
        choices=CHOIX_METHODE,
        widget=forms.RadioSelect,
        initial='ddr',
        label="Méthode de calcul"
    )
    
    date_dernieres_regles = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label="Date des dernières règles"
    )
    
    semaines_grossesse = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=42,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 20'
        }),
        label="Semaines de grossesse"
    )
    
    jours_grossesse = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=6,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-6 jours'
        }),
        label="Jours supplémentaires"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        methode = cleaned_data.get('methode')
        date_ddr = cleaned_data.get('date_dernieres_regles')
        semaines = cleaned_data.get('semaines_grossesse')
        
        if methode == 'ddr' and not date_ddr:
            raise forms.ValidationError("Veuillez entrer la date de vos dernières règles.")
        
        if methode == 'semaines' and not semaines:
            raise forms.ValidationError("Veuillez entrer le nombre de semaines de grossesse.")
        
        return cleaned_data