# mapli/apps.py
from django.apps import AppConfig

class MapliConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mapli'
    verbose_name = 'MaPli - Plateforme Maternité'
    
    def ready(self):
        """Initialisation de l'application"""
        # Importer les signaux si nécessaire
        try:
            import mapli.signals
        except ImportError:
            pass