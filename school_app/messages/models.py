from django.db import models
from django.contrib.auth.models import User

class MessageThread(models.Model):
    title = models.CharField(max_length=200,default="Title")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="authored_messages",
        null=True,        
    )
    recipients = models.ManyToManyField(User, related_name="massage_threads")
# Create your models here.
class Message(models.Model):
    thread = models.ForeignKey(MessageThread,related_name='messages', on_delete=models.CASCADE) 
    pub_date = models.DateTimeField("date published",auto_now_add=True)
    text = models.CharField(max_length=1500)
    sender = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
