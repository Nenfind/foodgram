from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from core.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_NAME


class User(AbstractUser):
    email = models.EmailField(max_length=MAX_LENGTH_EMAIL, unique=True)
    first_name = models.CharField(max_length=MAX_LENGTH_NAME)
    last_name = models.CharField(max_length=MAX_LENGTH_NAME)
    avatar = models.ImageField(
        null=True,
        blank=True,
        default=None,
        upload_to='users/avatars'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username', 'password']


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    subscription = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscription'],
                name='unique_subscription'
            )
        ]

    def clean(self):
        if self.user == self.subscription:
            raise ValidationError(
                'Нельзя подписаться на самого себя!'
            )
