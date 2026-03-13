from django.core.management.base import BaseCommand
from ..models import PregnancyCalendar, PregnancyMilestone, PregnancyChecklist

class Command(BaseCommand):
    help = 'Initialise les données du calendrier de grossesse pour toutes les semaines'

    def handle(self, *args, **options):
        self.stdout.write('Initialisation du calendrier de grossesse...')
        
        # Données pour chaque semaine
        weeks_data = {
            1: {
                'baby_size': '1-2 mm',
                'baby_weight': '< 1 g',
                'baby_development': 'L\'embryon commence à s\'implanter dans l\'utérus. Le tube neural se forme.',
                'mother_changes': 'Vous pouvez ressentir une fatigue inhabituelle. Les seins peuvent être tendus.',
                'nutrition_tips': 'Commencez à prendre de l\'acide folique. Buvez beaucoup d\'eau.',
                'medical_advice': 'Évitez l\'alcool et le tabac. Consultez votre médecin pour confirmer la grossesse.',
                'exercises': 'Marche douce, étirements légers.',
            },
            2: {
                'baby_size': '2-3 mm',
                'baby_weight': '< 1 g',
                'baby_development': 'Le cœur commence à battre. Les premiers vaisseaux sanguins se forment.',
                'mother_changes': 'Les nausées peuvent commencer. Les seins continuent de gonfler.',
                'nutrition_tips': 'Petits repas fréquents pour lutter contre les nausées.',
                'medical_advice': 'Première échographie de datation à prévoir.',
                'exercises': 'Yoga prénatal doux, respiration profonde.',
            },
            # ... Continuer pour toutes les semaines jusqu'à 42
        }
        
        # Créer les entrées de calendrier
        for week, data in weeks_data.items():
            calendar, created = PregnancyCalendar.objects.update_or_create(
                week_number=week,
                defaults={
                    'baby_size': data['baby_size'],
                    'baby_weight': data['baby_weight'],
                    'baby_development': data['baby_development'],
                    'mother_changes': data['mother_changes'],
                    'nutrition_tips': data['nutrition_tips'],
                    'medical_advice': data['medical_advice'],
                    'exercises': data['exercises'],
                }
            )
            
            if created:
                self.stdout.write(f'Semaine {week} créée')
            else:
                self.stdout.write(f'Semaine {week} mise à jour')
        
        # Créer les jalons importants
        milestones = [
            {
                'title': 'Début du 1er trimestre',
                'description': 'Félicitations, vous êtes enceinte ! Le développement de votre bébé commence.',
                'week_number': 1,
                'icon': 'star',
            },
            {
                'title': 'Première échographie',
                'description': 'C\'est le moment de votre première échographie de datation.',
                'week_number': 8,
                'icon': 'camera',
            },
            {
                'title': 'Début du 2ème trimestre',
                'description': 'Vous entrez dans le deuxième trimestre. Les nausées diminuent souvent.',
                'week_number': 14,
                'icon': 'flower',
            },
            {
                'title': 'Échographie morphologique',
                'description': 'Échographie détaillée pour vérifier le développement du bébé.',
                'week_number': 22,
                'icon': 'heart',
            },
            {
                'title': 'Début du 3ème trimestre',
                'description': 'Dernière ligne droite avant l\'arrivée de bébé !',
                'week_number': 27,
                'icon': 'baby',
            },
            {
                'title': 'Préparation à l\'accouchement',
                'description': 'Séances de préparation à la naissance recommandées.',
                'week_number': 32,
                'icon': 'hospital',
            },
            {
                'title': 'Dernière ligne droite',
                'description': 'Plus que quelques semaines avant la rencontre avec bébé.',
                'week_number': 36,
                'icon': 'clock',
            },
            {
                'title': 'Terme atteint',
                'description': 'Vous êtes à terme ! Bébé peut arriver à tout moment.',
                'week_number': 37,
                'icon': 'bell',
            },
        ]
        
        for milestone in milestones:
            obj, created = PregnancyMilestone.objects.update_or_create(
                title=milestone['title'],
                week_number=milestone['week_number'],
                defaults={
                    'description': milestone['description'],
                    'icon': milestone['icon'],
                }
            )
            
            if created:
                self.stdout.write(f'Jalon "{milestone["title"]}" créé')
        
        self.stdout.write(self.style.SUCCESS('Calendrier de grossesse initialisé avec succès !'))