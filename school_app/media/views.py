from django.shortcuts import render
from .models import ImageFile

def images_list(request):
    images = ImageFile.objects.all()
    return render(request, "images_list.html", {"images": images})