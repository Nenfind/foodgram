from django.contrib.auth import get_user_model
from django.db import models

from recipes.models import Recipe

User = get_user_model()

class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='ингредиенты',
    )
    user = models.ForeignKey(
        User,
        verbose_name='пользователь',
        related_name='shopping_cart',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'ingredients'),
                name='unique_ingredients_in_cart',
            )
        ]
        verbose_name = 'корзина покупок'
        verbose_name_plural = 'корзины покупок'

    def __str__(self):
        return f'Корзина пользователя {self.user.username}'
