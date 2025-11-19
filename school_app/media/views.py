from django.shortcuts import render
from .models import ImageFile,DocumentFile
from django.views.generic import CreateView

def images_list(request):
    images = ImageFile.objects.all()
    return render(request, "images_list.html", {"images": images})


class CreateImageView(CreateView):
    model = ImageFile
    template_name = 'images_list.html'
    success_url = '/media/images/'
    fields =['file']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = ImageFile.objects.all()
        context['documents'] = DocumentFile.objects.all()
        return context