"""
Backend SMTP Django avec bundle CA Mozilla (certifi).

- Windows / OpenSSL strict : erreurs type « Basic Constraints » -> certifi.where().
- « self-signed certificate in chain » : souvent antivirus / proxy (inspection TLS).
  Désactiver l’inspection SSL pour Python ou (dev uniquement) EMAIL_SMTP_INSECURE_TLS=1.
"""

import ssl
import warnings

from django.conf import settings as django_settings
from django.core.mail.backends.smtp import EmailBackend as DjangoSmtpEmailBackend
from django.utils.functional import cached_property


class CertifiEmailBackend(DjangoSmtpEmailBackend):
    @cached_property
    def ssl_context(self):
        if self.ssl_certfile or self.ssl_keyfile:
            ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
            return ssl_context

        insecure = getattr(django_settings, "EMAIL_SMTP_INSECURE_TLS", False)
        if insecure:
            warnings.warn(
                "EMAIL_SMTP_INSECURE_TLS actif : la connexion SMTP n’est pas authentifiée "
                "(risque d’attaque). Réservé au développement local derrière un antivirus/proxy.",
                UserWarning,
                stacklevel=1,
            )
            ctx = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx

        import certifi

        return ssl.create_default_context(cafile=certifi.where())
