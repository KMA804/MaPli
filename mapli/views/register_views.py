# views/register_views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from ..forms import (
    PatientRegistrationForm, 
    HospitalRegistrationForm, HospitalInfoForm, HospitalProfileForm,
    DoctorRegistrationForm, DoctorInfoForm, DoctorProfileForm
)
from ..models import UserRoles

def register_patient(request):
    """Inscription pour les patients"""
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Créer le profil patient
            from ..models import Patient
            Patient.objects.create(
                user=user,
                name=f"{user.first_name} {user.last_name}",
                date_of_birth=user.date_of_birth,
                phone_number=user.phone_number,
                email=user.email,
                country=user.country,
                province=user.province,
                commune=user.commune,
                current_district=user.district,
                blood_type=user.blood_type,
                allergies=user.allergies
            )
            login(request, user)
            messages.success(request, 'Inscription réussie ! Bienvenue sur MaPli.')
            return redirect('dashboard')
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'mapli/register/patient.html', {'form': form})
# views/admin_views.py

def register_hospital(request):
    """Inscription pour les hôpitaux"""
    if request.method == 'POST':
        user_form = HospitalRegistrationForm(request.POST)
        hospital_form = HospitalInfoForm(request.POST)
        profile_form = HospitalProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and hospital_form.is_valid() and profile_form.is_valid():
            # Créer l'utilisateur
            user = user_form.save()
            
            # Créer l'hôpital
            hospital = hospital_form.save()
            
            # Créer le profil hôpital
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.hospital = hospital
            profile.save()
            
            messages.success(
                request, 
                'Votre demande d\'inscription a été envoyée. '
                'Un administrateur validera votre compte sous 48h.'
            )
            return redirect('index')
    else:
        user_form = HospitalRegistrationForm()
        hospital_form = HospitalInfoForm()
        profile_form = HospitalProfileForm()
    
    context = {
        'user_form': user_form,
        'hospital_form': hospital_form,
        'profile_form': profile_form,
    }
    return render(request, 'mapli/register/hospital.html', context)

def register_doctor(request):
    """Inscription pour les médecins"""
    if request.method == 'POST':
        user_form = DoctorRegistrationForm(request.POST)
        doctor_form = DoctorInfoForm(request.POST)
        profile_form = DoctorProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and doctor_form.is_valid() and profile_form.is_valid():
            # Créer l'utilisateur
            user = user_form.save()
            
            # Créer le docteur
            doctor = doctor_form.save(commit=False)
            doctor.name = f"{user.first_name} {user.last_name}"
            doctor.save()
            
            # Créer le profil docteur
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.doctor = doctor
            profile.save()
            
            messages.success(
                request, 
                'Votre demande d\'inscription a été envoyée. '
                'Un administrateur validera votre compte sous 48h.'
            )
            return redirect('index')
    else:
        user_form = DoctorRegistrationForm()
        doctor_form = DoctorInfoForm()
        profile_form = DoctorProfileForm()
    
    context = {
        'user_form': user_form,
        'doctor_form': doctor_form,
        'profile_form': profile_form,
    }
    return render(request, 'mapli/register/doctor.html', context)