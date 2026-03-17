from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Crée un superutilisateur si aucun n\'existe'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Noone')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'kanakimanamarieange8@gmail.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Ange@2222')
            
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superutilisateur "{username}" créé avec succès'))
        else:
            self.stdout.write('Un superutilisateur existe déjà')