# views.py
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from datetime import datetime, timedelta, time
from ..models import Speciality, Doctor, Patient, Pregnancy, Appointment, PregnancyAppointment, Hospital
from ..serializers import *
from .mail import send_appointment_confirmation_email

class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    permission_classes = [AllowAny]

class SpecialityViewSet(viewsets.ModelViewSet):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer
    permission_classes = [AllowAny]

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()  
    serializer_class = DoctorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Filtre les médecins par hôpital si hospital_id est fourni
        """
        queryset = super().get_queryset()
        hospital_id = self.request.query_params.get('hospital_id')
        
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)
        
        return queryset
  
class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [AllowAny]

class PregnancyViewSet(viewsets.ModelViewSet):
    queryset = Pregnancy.objects.all()
    serializer_class = PregnancySerializer
    permission_classes = [AllowAny]

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().order_by('-created_at')
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateAppointmentSerializer
        return AppointmentSerializer

    def create(self, request, *args, **kwargs):
        """
        Créer un rendez-vous avec vérification des coordonnées utilisateur et conflits horaires
        """
        try:
            data = request.data
            
            # VÉRIFICATION SI L'UTILISATEUR EST CONNECTÉ
            if not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'error': 'Vous devez être connecté pour prendre un rendez-vous'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # RÉCUPÉRATION DES DONNÉES DE L'UTILISATEUR CONNECTÉ
            user = request.user
            getattr(user, 'userprofile', None)

            # VÉRIFICATION DE LA CORRESPONDANCE DES COORDONNÉES
            patient_name = data.get('patient_name', '').strip()
            _raw_email = data.get('patient_email', '')
            if isinstance(_raw_email, list):
                _raw_email = _raw_email[0] if _raw_email else ''
            patient_email = str(_raw_email).strip().lower()
            patient_phone = data.get('patient_phone', '').strip()
            
            # Construction du nom complet utilisateur
            user_full_name = f"{user.first_name} {user.last_name}".strip()
            
            # VÉRIFICATION DU NOM
            if patient_name.lower() != user_full_name.lower():
                return Response({
                    'success': False,
                    'error': f'Le nom doit correspondre à votre compte. Votre nom: {user_full_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # E-mail de contact / envoi du reçu : libre (toute adresse valide), pas obligé d’être celle du compte
            if not patient_email or '@' not in patient_email:
                return Response({
                    'success': False,
                    'error': 'Une adresse e-mail valide est requise pour recevoir la confirmation et le PDF.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # VÉRIFICATION DU TÉLÉPHONE (si disponible dans le profil)
            if hasattr(user, 'phone_number') and user.phone_number:
                if patient_phone != user.phone_number:
                    return Response({
                        'success': False,
                        'error': f'Le numéro de téléphone doit correspondre à votre compte. Votre numéro: {user.phone_number}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # VALIDATION FORMAT DATE/HEURE
            scheduled_date_str = data.get('scheduled_date')
            if not scheduled_date_str:
                return Response({
                    'success': False,
                    'error': 'La date et heure sont requises'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Conversion en datetime
            try:
                # Format attendu: "2024-01-15 14:30"
                scheduled_datetime = datetime.strptime(scheduled_date_str, "%Y-%m-%d %H:%M")
                if timezone.is_naive(scheduled_datetime):
                    scheduled_datetime = timezone.make_aware(
                        scheduled_datetime, timezone.get_current_timezone()
                    )
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Format de date/heure invalide. Utilisez: YYYY-MM-DD HH:MM'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # VÉRIFICATION CONFLIT HORAIRE
            conflicting_appointment = Appointment.objects.filter(
                doctor_id=data['doctor'],
                scheduled_date=scheduled_datetime
            ).first()
            
            if conflicting_appointment:
                heure_occupee = scheduled_datetime.strftime("%H:%M")
                return Response({
                    'success': False,
                    'error': f'Le médecin est déjà occupé à {heure_occupee}. Veuillez choisir une autre heure.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # VÉRIFICATION CAPACITÉ JOURNALIÈRE (24 RDV max)
            appointment_date = scheduled_datetime.date()
            daily_count = Appointment.objects.filter(
                hospital_id=data['hospital'],
                appointment_date=appointment_date,
                is_confirmed=True
            ).count()
            
            if daily_count >= 24:
                return Response({
                    'success': False,
                    'error': 'Capacité maximale atteinte pour cette date (24 rendez-vous maximum). Veuillez choisir une autre date.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # VÉRIFICATION HEURES DE TRAVAIL (7h-12h et 14h-17h)
            appointment_time = scheduled_datetime.time()
            morning_start = time(7, 0)
            morning_end = time(12, 0)
            afternoon_start = time(14, 0)
            afternoon_end = time(17, 0)
            
            if not ((morning_start <= appointment_time <= morning_end) or 
                   (afternoon_start <= appointment_time <= afternoon_end)):
                return Response({
                    'success': False,
                    'error': 'Les rendez-vous sont disponibles de 7h-12h et 14h-17h uniquement. Veuillez choisir une heure dans ces plages.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # VÉRIFICATION WEEK-END
            if scheduled_datetime.weekday() >= 5:
                return Response({
                    'success': False,
                    'error': 'Les rendez-vous ne sont pas disponibles le week-end. Veuillez choisir un jour en semaine.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer le docteur et l'hôpital
            try:
                doctor = Doctor.objects.get(id=data['doctor'])
                hospital = Hospital.objects.get(id=data['hospital'])
            except (Doctor.DoesNotExist, Hospital.DoesNotExist):
                return Response({
                    'success': False,
                    'error': 'Docteur ou hôpital non trouvé'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier que le docteur appartient à l'hôpital sélectionné
            if doctor.hospital != hospital:
                return Response({
                    'success': False,
                    'error': 'Le docteur sélectionné ne fait pas partie de cet hôpital'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer ou récupérer le patient
            patient_data = {
                'name': data['patient_name'],
                'phone_number': data['patient_phone'],
                'date_of_birth': '2000-01-01',  # Valeur par défaut
                'nationality': 'Non spécifiée',
                'country': 'République Démocratique du Congo',
                'province': 'Non spécifiée',
                'commune': 'Non spécifiée',
                'current_district': 'Non spécifié',
            }
            
            patient, created = Patient.objects.get_or_create(
                email=patient_email,
                defaults=patient_data,
            )
            
            # Mettre à jour si le patient existe déjà
            if not created:
                patient.name = patient_name
                patient.phone_number = patient_phone
                patient.save()
            
            # CRÉATION du rendez-vous AVEC L'UTILISATEUR ASSOCIÉ
            appointment = Appointment.objects.create(
                patient_name=patient_name,
                patient_email=patient_email,
                patient_phone=patient_phone,
                doctor=doctor,
                hospital=hospital,
                scheduled_date=scheduled_datetime,
                reason=data.get('reason', ''),
                ultrasound_type=data.get('ultrasound_type', ''),
                pregnancy_week=data.get('pregnancy_week'),
                user=user  # ASSOCIATION AVEC L'UTILISATEUR CONNECTÉ
            )

            confirmation_email_sent, email_send_error = send_appointment_confirmation_email(
                appointment
            )

            payload = {
                'success': True,
                'message': (
                    'Rendez-vous créé avec succès. Un e-mail de confirmation avec le reçu PDF vous a été envoyé.'
                    if confirmation_email_sent
                    else 'Rendez-vous créé avec succès. L’envoi de l’e-mail a échoué : téléchargez le reçu PDF sur la page de confirmation ou vérifiez la configuration SMTP (.env).'
                ),
                'appointment_id': appointment.id,
                'registration_number': str(appointment.registration_number),
                'redirect_url': f"/appointment/success/{appointment.id}/",
                'confirmation_email_sent': confirmation_email_sent,
            }
            if settings.DEBUG and not confirmation_email_sent and email_send_error:
                payload['email_send_error'] = email_send_error

            return Response(payload, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Création rendez-vous: %s", e)
            return Response({
                'success': False,
                'error': f'Erreur lors de la création du rendez-vous: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def available_time_slots(self, request):
        """
        Retourne les créneaux horaires disponibles pour un médecin à une date donnée
        """
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')
        
        if not doctor_id or not date_str:
            return Response({"error": "doctor_id et date sont requis"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Conversion de la date
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Vérification week-end
            if target_date.weekday() >= 5:
                return Response({
                    "available_slots": [],
                    "message": "Aucun rendez-vous disponible le week-end"
                })
            
            # Heures de travail
            time_slots = []
            
            # Matin: 7h-12h (toutes les 20 minutes)
            for hour in range(7, 12):
                for minute in [0, 20, 40]:
                    time_slots.append(time(hour, minute))
            
            # Après-midi: 14h-17h (toutes les 20 minutes)
            for hour in range(14, 17):
                for minute in [0, 20, 40]:
                    time_slots.append(time(hour, minute))
            
            # Récupérer les rendez-vous existants
            existing_appointments = Appointment.objects.filter(
                doctor_id=doctor_id,
                scheduled_date__date=target_date
            ).values_list('scheduled_date', flat=True)
            
            # Convertir en heures occupées
            occupied_times = [appt.time() for appt in existing_appointments]
            
            # Filtrer les créneaux disponibles
            available_slots = []
            for slot in time_slots:
                if slot not in occupied_times:
                    available_slots.append(slot.strftime("%H:%M"))
            
            return Response({
                "date": date_str,
                "available_slots": available_slots,
                "total_slots": len(available_slots),
                "message": f"{len(available_slots)} créneaux disponibles"
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PregnancyAppointmentViewSet(viewsets.ModelViewSet):
    queryset = PregnancyAppointment.objects.all()
    serializer_class = PregnancyAppointmentSerializer
    permission_classes = [AllowAny]