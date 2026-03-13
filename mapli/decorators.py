# decorators.py
from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps

def role_required(required_role, login_url=None):
    """
    Décorateur pour restreindre l'accès à un rôle spécifique
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si l'utilisateur est authentifié
            if not request.user.is_authenticated:
                return redirect(login_url or 'index')
            
            # Vérifier si l'utilisateur a l'attribut 'role'
            if not hasattr(request.user, 'role'):
                messages.error(request, "Erreur de configuration utilisateur.")
                return redirect('dashboard')
            
            # Vérifier le rôle
            if request.user.role == required_role:
                return view_func(request, *args, **kwargs)
            
            # Message d'erreur et redirection
            messages.error(request, "Vous n'avez pas les permissions pour accéder à cette page.")
            return redirect('dashboard')
        return _wrapped_view
    return decorator