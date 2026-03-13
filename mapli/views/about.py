from django.shortcuts import render
from django.contrib.auth.decorators import login_required
@login_required
def about(request):
    return render(request, 'mapli/about.html')