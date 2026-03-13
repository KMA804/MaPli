from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from ..models import UserProfile  # Assurez-vous que le chemin d'import est correct

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """API pour récupérer les données du profil utilisateur"""
    user = request.user
    
    try:
        # Récupérer le profil utilisateur
        user_profile = UserProfile.objects.get(user=user)
        
        profile_data = {
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'email': user.email or '',
            'username': user.username,
            'phone_number': user_profile.phone_number or '',
            'date_of_birth': user_profile.date_of_birth or '',
            'country': user_profile.country or '',
            'province': user_profile.province or '',
            'commune': user_profile.commune or '',
            'district': user_profile.district or '',
            'job_title': user_profile.job_title or '',
            'is_pregnant': user_profile.is_pregnant or False,
            'current_pregnancy_week': user_profile.current_pregnancy_week or '',
            'last_menstrual_period': user_profile.last_menstrual_period or '',
            'blood_type': user_profile.blood_type or '',
            'allergies': user_profile.allergies or ''
        }
        
    except UserProfile.DoesNotExist:
        # Si pas de profil, retourner juste les données de base
        profile_data = {
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'email': user.email or '',
            'username': user.username,
            'phone_number': '',
            'date_of_birth': '',
            'country': '',
            'province': '',
            'commune': '',
            'district': '',
            'job_title': '',
            'is_pregnant': False,
            'current_pregnancy_week': '',
            'last_menstrual_period': '',
            'blood_type': '',
            'allergies': ''
        }
    
    return Response(profile_data)