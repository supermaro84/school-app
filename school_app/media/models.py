from django.core.files.storage import FileSystemStorage
from django.db import models
import os
# Create your models here.
def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return f'images/{instance.owner.id}/{filename}'
class ImageFile(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, default=1)
    file = models.ImageField(upload_to=user_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class DocumentFile(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, default=1)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    @property
    def filename(self):
        return os.path.basename(self.file.name)
    
    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1]
    
    @property
    def file_size(self):
        if self.file:
            return self.file.size
        return 0