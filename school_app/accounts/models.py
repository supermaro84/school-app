from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birthdate = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def age(self):
        """Calculate age from birthdate"""
        if self.birthdate:
            from datetime import date
            today = date.today()
            return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return None


# Automatically create/save profile when user is created/saved
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
