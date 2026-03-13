# votre_app/management/commands/migrate_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mapli.models import UserRoles  # Adaptez le nom de votre app

User = get_user_model()

class Command(BaseCommand):
    help = 'Migrer les utilisateurs existants vers le nouveau système de rôles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler la migration sans sauvegarder',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('Début de la migration des rôles...'))
        
        # Récupérer tous les utilisateurs sans rôle
        users_without_role = User.objects.filter(role__isnull=True)
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'*** MODE SIMULATION ***'))
        
        self.stdout.write(f"Utilisateurs trouvés sans rôle : {users_without_role.count()}")
        
        updated_count = 0
        skipped_count = 0
        
        for user in users_without_role:
            # Déterminer le rôle basé sur les données existantes
            old_role = user.role if hasattr(user, 'role') else 'Non défini'
            
            if user.is_superuser:
                new_role = UserRoles.ADMIN_SYSTEME
                reason = "superuser"
            elif hasattr(user, 'doctor_profile') and user.doctor_profile:
                new_role = UserRoles.MEDECIN
                reason = "a un profil médecin"
            elif hasattr(user, 'hospital_profile') and user.hospital_profile:
                new_role = UserRoles.HOPITAL
                reason = "a un profil hôpital"
            elif hasattr(user, 'patient_profile') and user.patient_profile:
                new_role = UserRoles.PATIENT
                reason = "a un profil patient"
            else:
                # Par défaut, patient
                new_role = UserRoles.PATIENT
                reason = "rôle par défaut"
            
            # Afficher ce qui va être fait
            self.stdout.write(
                f"  {user.username} ({user.email}): "
                f"{old_role} → {new_role} ({reason})"
            )
            
            if not dry_run:
                user.role = new_role
                user.save()
                updated_count += 1
            else:
                updated_count += 1
        
        # Résumé
        self.stdout.write(self.style.SUCCESS(
            f'\nMigration terminée ! {updated_count} utilisateurs traités.'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                'Mode simulation : AUCUNE modification réelle effectuée.\n'
                'Exécutez sans --dry-run pour appliquer les changements.'
            ))