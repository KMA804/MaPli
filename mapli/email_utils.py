"""Utilitaires pour savoir si un e-mail est réellement envoyé sur Internet."""

from django.conf import settings


def email_backend_delivers_to_internet() -> bool:
    """
    False pour console, fichier, mémoire, etc. — send() réussit mais aucune livraison réelle.
    """
    backend = (settings.EMAIL_BACKEND or "").lower()
    non_network = (
        "console",
        "filebased",
        "locmem",
        "dummy",
        "cache",
    )
    return not any(fragment in backend for fragment in non_network)
