from django.contrib.auth.models import AbstractUser
from django.db import models

from users.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_NAME


class User(AbstractUser):
    """
    Custom User model for Foodgram project.
    All fields except avatar are required,
    username field is email.
    """

    email = models.EmailField(max_length=MAX_LENGTH_EMAIL, unique=True)
    first_name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        blank=False
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        blank=False
    )
    avatar = models.ImageField(
        null=True,
        blank=True,
        default=None,
        upload_to='users/avatars'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']


class Subscription(models.Model):
    """Model for user-to-user subscriptions."""

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
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("subscription")),
                name="prevent_self_subscription",
            ),
        ]
