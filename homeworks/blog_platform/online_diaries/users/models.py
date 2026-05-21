# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserWithImage(AbstractUser):
    profile_image = models.ImageField(
        "Profile Image", upload_to="profile_images/", blank=True, default="profile_images/default_avatar.jpeg"
    )
