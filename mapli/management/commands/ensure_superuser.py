from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Crée un superutilisateur si aucun n\'existe'

    def add_arguments(self, parser):
        # Ajout de l'argument --no-input
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Désactive les invites interactives',
        )
        parser.add_argument(
            '--username',
            default=None,
            help="Nom d'utilisateur pour le superutilisateur"
        )
        parser.add_argument(
            '--email',
            default=None,
            help="Email pour le superutilisateur"
        )
        parser.add_argument(
            '--password',
            default=None,
            help="Mot de passe pour le superutilisateur"
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Vérifier si un superutilisateur existe déjà
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.SUCCESS('✓ Un superutilisateur existe déjà. Aucune action nécessaire.')
            )
            return

        self.stdout.write(self.style.WARNING('🔧 Aucun superutilisateur trouvé. Création en cours...'))

        # Récupérer les informations
        username = options['username'] or os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = options['email'] or os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = options['password'] or os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

        # Création du superutilisateur
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Superutilisateur "{username}" créé avec succès !')
        )