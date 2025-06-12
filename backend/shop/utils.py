from datetime import datetime as dt

from django.db.models import Sum

from core.constants import DATETIME_FORMAT
from recipes.models import Ingredient


def create_shopping_list(user) -> str:
    """
    Creates shopping list and groups all the ingredients
    by their names.
    """
    ingredients = (
        Ingredient.objects.filter(
            recipeingredient__recipe__in_shopping_cart__user=user
        )
        .annotate(
            total_amount=Sum('recipeingredient__amount'),
        )
        .values('name', 'measurement_unit', 'total_amount')
        .order_by('name')
    )
    shopping_list = [
        f'{ing["name"]} ({ing["measurement_unit"]}): {ing["total_amount"]}'
        for ing in ingredients
    ]
    shopping_list.insert(
        0,
        ("Список покупок пользователя:"
         f"\n\n{user.get_full_name() or user.username}\n"
         f"{dt.now().strftime(DATETIME_FORMAT)}\n")
    )
    shopping_list.append("\n\nПриятной готовки!")
    return ('\n'.join(shopping_list))
