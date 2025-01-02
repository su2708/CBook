from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):   
    phone = models.CharField(max_length=13, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    gender = models.BooleanField(default=True) #True='남자' False='여자'
    last_login = models.DateTimeField(default=timezone.now)
    
    REQUIRED_FIELDS = ["phone"]
    
    def __str__(self):
        return self.username