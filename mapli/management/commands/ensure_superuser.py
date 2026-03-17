# mapli/management/commands/ensure_superuser.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import os
import sys

class Command(BaseCommand):
    help = 'Crée un superutilisateur si aucun n\'existe, avec gestion sécurisée des mots de passe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default=None,
            help="Nom d'utilisateur pour le superutilisateur (prioritaire sur la variable d'env)"
        )
        parser.add_argument(
            '--email',
            default=None,
            help="Email pour le superutilisateur (prioritaire sur la variable d'env)"
        )
        parser.add_argument(
            '--password',
            default=None,
            help="Mot de passe pour le superutilisateur (prioritaire sur la variable d'env)"
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

        # Récupérer les informations dans l'ordre : ligne de commande > variables d'env > valeurs par défaut
        username = options['username'] or os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = options['email'] or os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = options['password'] or os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        # Validation des entrées
        if not username:
            username = 'admin'
            self.stdout.write(
                self.style.WARNING(f'⚠️  Nom d\'utilisateur non fourni, utilisation de "{username}" par défaut')
            )
        
        if not email:
            email = 'admin@example.com'
            self.stdout.write(
                self.style.WARNING(f'⚠️  Email non fourni, utilisation de "{email}" par défaut')
            )
        
        if not password:
            # Générer un mot de passe aléatoire sécurisé si aucun n'est fourni
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(alphabet) for _ in range(16))
            self.stdout.write(
                self.style.WARNING('⚠️  Mot de passe non fourni, un mot de passe sécurisé a été généré')
            )
            self.stdout.write(
                self.style.SUCCESS(f'🔐 Mot de passe généré : {password}')
            )
            self.stdout.write(
                self.style.WARNING('⚠️  IMPORTANT : Notez ce mot de passe maintenant ! Il ne sera plus affiché.')
            )

        try:
            # Création du superutilisateur
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superutilisateur "{username}" créé avec succès !')
            )
            
            # Afficher des informations utiles
            self.stdout.write(self.style.SUCCESS(f'📧 Email : {email}'))
            if not options['password'] and not os.environ.get('DJANGO_SUPERUSER_PASSWORD'):
                self.stdout.write(self.style.SUCCESS(f'🔐 Mot de passe : {password} (notez-le !)'))
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur d\'intégrité : {str(e)}')
            )
            sys.exit(1)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur inattendue : {str(e)}')
            )
            sys.exit(1)