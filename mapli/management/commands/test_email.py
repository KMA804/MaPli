import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError

from mapli.email_utils import email_backend_delivers_to_internet

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Envoie un e-mail de test (vérifie SMTP / .env). "
        "Usage : python manage.py test_email destinataire@example.com"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "recipient",
            nargs="?",
            default="",
            help="Adresse qui doit recevoir le message (défaut : EMAIL_HOST_USER)",
        )

    def handle(self, *args, **options):
        recipient = (options["recipient"] or "").strip()
        if not recipient:
            recipient = (settings.EMAIL_HOST_USER or "").strip()
        if not recipient:
            raise CommandError(
                "Indiquez une adresse : python manage.py test_email vous@gmail.com "
                "ou définissez EMAIL_HOST_USER dans .env."
            )

        self.stdout.write(f"EMAIL_BACKEND = {settings.EMAIL_BACKEND!r}")
        self.stdout.write(f"EMAIL_HOST = {settings.EMAIL_HOST!r} port {settings.EMAIL_PORT}")
        self.stdout.write(f"FROM = {settings.DEFAULT_FROM_EMAIL!r} -> TO = {recipient!r}")

        if not email_backend_delivers_to_internet():
            self.stdout.write(
                self.style.WARNING(
                    "Ce backend ne livre pas sur Internet : le message ira dans la console "
                    "ou un fichier, pas dans une boîte Gmail."
                )
            )

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise CommandError(
                "EMAIL_HOST_USER et EMAIL_HOST_PASSWORD doivent être définis dans .env pour le SMTP."
            )

        try:
            send_mail(
                subject="MaPli — test SMTP",
                message="Si vous lisez ceci, la configuration e-mail fonctionne.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception as e:
            raise CommandError(f"Échec SMTP : {e}") from e

        self.stdout.write(self.style.SUCCESS(f"Message accepté par le serveur SMTP pour {recipient}."))
        self.stdout.write(
            "Si rien n'arrive : spam / onglet Promotions (Gmail), delai de quelques minutes. "
            "Testez aussi une autre adresse : python manage.py test_email autre@gmail.com"
        )
        self.stdout.write(
            "Pour un compte Gmail personnel comme SMTP : la livraison vers d'autres boites "
            "depend surtout des filtres (spam). En production, preferez un service transactionnel "
            "(SendGrid, Resend, etc.) avec domaine verifie."
        )
