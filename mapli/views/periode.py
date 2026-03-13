# Fichier: mapli/views/periode.py

from django.shortcuts import render, redirect
from django.contrib import messages
from ..forms import PeriodeGrossesseForm
import json

def validation_periode(request):
    if request.method == 'POST':
        form = PeriodeGrossesseForm(request.POST)
        if form.is_valid():
            # Stocker le trimestre en session
            request.session['trimestre'] = form.cleaned_data['trimestre']
            request.session['exercices_authorized'] = True
            return redirect('exercices_adaptes')
    else:
        form = PeriodeGrossesseForm()
    
    return render(request, 'mapli/validation_periode.html', {'form': form})

def exercices_adaptes(request):
    # Vérifier si l'utilisateur a validé sa période
    if not request.session.get('exercices_authorized'):
        messages.warning(request, "Veuillez d'abord valider votre période de grossesse.")
        return redirect('validation_periode')
    
    trimestre = request.session.get('trimestre')
    
    # Données des exercices par trimestre
    exercices_data = {
        '1': {
            'title': 'Exercices pour le 1er trimestre',
            'description': 'Des mouvements doux pour vous accompagner en début de grossesse',
            'exercices': [
                {
                    'nom': 'Respiration profonde',
                    'description': 'Exercice de respiration pour gérer les nausées et le stress',
                    'duree': '5-10 minutes',
                    'video': 'assets/videos/respiration-1er.mp4'
                },
                {
                    'nom': 'Marche légère',
                    'description': 'Activation circulatoire en douceur',
                    'duree': '15-30 minutes',
                    'video': 'assets/videos/marche.mp4'
                }
            ]
        },
        '2': {
            'title': 'Exercices pour le 2ème trimestre',
            'description': 'Activités adaptées à votre énergie retrouvée',
            'exercices': [
                {
                    'nom': 'Yoga prénatal',
                    'description': 'Postures douces pour assouplir le corps',
                    'duree': '20 minutes',
                    'video': 'assets/videos/yoga-2cnd.mp4'
                },
                {
                    'nom': 'Exercices du plancher pelvien',
                    'description': 'Renforcement en douceur',
                    'duree': '10 minutes',
                    'video': 'assets/videos/pelvien.mp4'
                }
            ]
        },
        '3': {
            'title': 'Exercices pour le 3ème trimestre',
            'description': 'Préparation en douceur pour l\'accouchement',
            'exercices': [
                {
                    'nom': 'Respiration de préparation',
                    'description': 'Techniques de respiration pour l\'accouchement',
                    'duree': '15 minutes',
                    'video': 'assets/videos/respiration-1er.mp4'
                },
                {
                    'nom': 'Mouvements du bassin',
                    'description': 'Soulager les douleurs lombaires',
                    'duree': '10 minutes',
                    'video': 'assets/videos/bassin.mp4'
                }
            ]
        }
    }
    
    data = exercices_data.get(trimestre, {})
    
    # Convertir les exercices en JSON pour le template
    context = {
        'data': data,
        'exercices_json': json.dumps(data.get('exercices', [])),
        'trimestre': trimestre
    }
    
    return render(request, 'mapli/exercices_adaptes.html', context)