from django_filters import rest_framework as filters

from api.utils import filter_by_relation, get_user_from_context
from recipes.models import Favorite, Recipe, Tag
from shop.models import ShoppingCart


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags',]

    def filter_favorited(self, queryset, name, value):
        user = get_user_from_context(self.request)
        return filter_by_relation(queryset, user, Favorite, value)

    def filter_shopping_cart(self, queryset, name, value):
        user = get_user_from_context(self.request)
        return filter_by_relation(queryset, user, ShoppingCart, value)