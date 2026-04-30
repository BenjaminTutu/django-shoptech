

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# Create your models here.

class User(AbstractUser):
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    address = models.TextField( null=True, blank=True)
    date_joined = models.DateField(default=timezone.now)
    role = models.CharField(max_length=11, choices=[
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    ], default='customer'
                            )

    def __str__(self):
        return self.email

    def is_admin(self):
        return self.role == 'admin'


