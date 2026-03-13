from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()

class Command(BaseCommand):
    help = 'Vérifier les rôles utilisateurs'

    def handle(self, *args, **options):
        self.stdout.write("Répartition des rôles :")
        self.stdout.write("-" * 40)
        
        # Compter par rôle
        roles_count = User.objects.values('role').annotate(
            total=Count('id')
        ).order_by('role')
        
        for item in roles_count:
            role = item['role']
            count = item['total']
            self.stdout.write(f"Rôle {role}: {count} utilisateurs")
        
        self.stdout.write("-" * 40)
        self.stdout.write(f"TOTAL: {User.objects.count()} utilisateurs")