# serializers.py
from rest_framework import serializers
from .models import Speciality, Doctor, Patient, Pregnancy, Appointment, PregnancyAppointment, Hospital, PatientSession

class SpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'address', 'latitude', 'longitude', 
            'phone_number', 'email', 'has_ultrasound', 'has_maternity', 'services'
        ]
        read_only_fields = ['id']

class DoctorSerializer(serializers.ModelSerializer):
    speciality = SpecialitySerializer(read_only=True)
    hospital = HospitalSerializer(read_only=True)
    full_name = serializers.CharField(source='name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            'id', 'name', 'full_name', 'email', 'speciality', 'hospital',
            'address', 'phone_number', 'is_available'
        ]
        read_only_fields = ['id']

class DoctorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            'name', 'email', 'speciality', 'hospital', 'address', 
            'phone_number', 'is_available'
        ]

class PatientSerializer(serializers.ModelSerializer):
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'name', 'date_of_birth', 'nationality', 'country', 
            'province', 'commune', 'current_district', 'address', 'full_address',
            'phone_number', 'email', 'blood_type', 'allergies', 
            'latitude', 'longitude'
        ]
        read_only_fields = ['id']

class PatientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'name', 'date_of_birth', 'nationality', 'country', 'province',
            'commune', 'current_district', 'address', 'phone_number', 'email',
            'blood_type', 'allergies', 'latitude', 'longitude'
        ]

class PregnancySerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(), 
        source='patient',
        write_only=True
    )
    
    class Meta:
        model = Pregnancy
        fields = [
            'id', 'patient', 'patient_id', 'start_date', 'estimated_delivery_date',
            'current_trimester', 'is_active'
        ]
        read_only_fields = ['id', 'estimated_delivery_date']

class AppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    hospital = HospitalSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(),
        source='doctor',
        write_only=True
    )
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(),
        source='hospital',
        write_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_name', 'patient_email', 'patient_phone',
            'doctor', 'doctor_id', 'hospital', 'hospital_id',
            'scheduled_date', 'status', 'status_display', 'reason',
            'ultrasound_type', 'pregnancy_week', 'created_at', 'registration_number'
        ]
        read_only_fields = ['id', 'created_at', 'registration_number']

class CreateAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'patient_name', 'patient_email', 'patient_phone', 'doctor', 'hospital',
            'scheduled_date', 'reason', 'ultrasound_type', 'pregnancy_week'
        ]

class PublicAppointmentSerializer(serializers.ModelSerializer):
    """Serializer pour la création de rendez-vous sans authentification"""
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.filter(is_available=True),
        source='doctor'
    )
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(),
        source='hospital'
    )
    
    class Meta:
        model = Appointment
        fields = [
            'patient_name', 'patient_email', 'patient_phone', 
            'doctor_id', 'hospital_id', 'scheduled_date', 
            'reason', 'ultrasound_type', 'pregnancy_week'
        ]
    
    def validate(self, data):
        # Vérifier que le docteur appartient à l'hôpital sélectionné
        doctor = data.get('doctor')
        hospital = data.get('hospital')
        
        if doctor and hospital and doctor.hospital != hospital:
            raise serializers.ValidationError({
                'doctor': 'Le docteur sélectionné ne fait pas partie de cet hôpital'
            })
        
        # Vérifier que le créneau n'est pas déjà pris
        scheduled_date = data.get('scheduled_date')
        if scheduled_date and doctor:
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                scheduled_date=scheduled_date
            ).exists()
            
            if existing_appointment:
                raise serializers.ValidationError({
                    'scheduled_date': 'Ce créneau horaire est déjà réservé pour ce médecin'
                })
        
        return data

class PregnancyAppointmentSerializer(serializers.ModelSerializer):
    # Hérite de tous les champs de Appointment
    doctor = DoctorSerializer(read_only=True)
    hospital = HospitalSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(),
        source='doctor',
        write_only=True
    )
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(),
        source='hospital',
        write_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    appointment_type_display = serializers.CharField(source='get_appointment_type_display', read_only=True)
    trimester_display = serializers.CharField(source='get_trimester_display', read_only=True)
    
    class Meta:
        model = PregnancyAppointment
        fields = [
            'id', 'patient_name', 'patient_email', 'patient_phone',
            'doctor', 'doctor_id', 'hospital', 'hospital_id',
            'scheduled_date', 'status', 'status_display', 'reason',
            'ultrasound_type', 'pregnancy_week', 'created_at', 'registration_number',
            'appointment_type', 'appointment_type_display', 'trimester', 'trimester_display',
            'is_anomaly_detected', 'notes'
        ]
        read_only_fields = ['id', 'created_at', 'registration_number']

class PatientSessionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    selected_hospital = HospitalSerializer(read_only=True)
    
    class Meta:
        model = PatientSession
        fields = ['id', 'patient', 'selected_hospital', 'created_at']
        read_only_fields = ['id', 'created_at']

# Serializers pour les statistiques et rapports
class AppointmentStatsSerializer(serializers.Serializer):
    total_appointments = serializers.IntegerField()
    pending_appointments = serializers.IntegerField()
    confirmed_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    cancelled_appointments = serializers.IntegerField()

class DoctorStatsSerializer(serializers.Serializer):
    doctor = DoctorSerializer(read_only=True)
    total_appointments = serializers.IntegerField()
    upcoming_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()

class HospitalStatsSerializer(serializers.Serializer):
    hospital = HospitalSerializer(read_only=True)
    total_doctors = serializers.IntegerField()
    total_appointments = serializers.IntegerField()
    available_doctors = serializers.IntegerField()

# Serializer pour la recherche de créneaux disponibles
class AvailableSlotsRequestSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    date = serializers.DateField()

class AvailableSlotsResponseSerializer(serializers.Serializer):
    available_slots = serializers.ListField(
        child=serializers.CharField()
    )

# Serializers pour les filtres
class AppointmentFilterSerializer(serializers.Serializer):
    doctor = serializers.IntegerField(required=False)
    hospital = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

class DoctorFilterSerializer(serializers.Serializer):
    hospital = serializers.IntegerField(required=False)
    speciality = serializers.IntegerField(required=False)
    is_available = serializers.BooleanField(required=False)