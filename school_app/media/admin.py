from django.contrib import admin

from .models import ImageFile,DocumentFile

admin.site.register(ImageFile)
admin.site.register(DocumentFile)