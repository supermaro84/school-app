from django.core.files.storage import FileSystemStorage
from django.db import models
# Create your models here.
class ImageFile(models.Model):
    file = models.ImageField(upload_to="")  # EMPTY! S3Storage already puts it inside /media/
    uploaded_at = models.DateTimeField(auto_now_add=True)