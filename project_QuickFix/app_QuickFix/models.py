from django.db import models

from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_common = models.BooleanField(default=True)

    # Você pode adicionar outros campos personalizados aqui
    # exemplo: data_nascimento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.username