from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

@login_required
def faq_view(request):
    """
    Vue fonctionnelle pour afficher la FAQ
    """
    context = {
        'page_title': "Questions fréquentes - MaPli",
        'total_questions': 15,
        'popular_categories': ['Grossesse', 'Rendez-vous', 'Nutrition'],
    }
    return render(request, 'mapli/faq.html', context)