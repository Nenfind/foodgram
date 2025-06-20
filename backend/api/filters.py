from django.db.models import Case, IntegerField, Q, Value, When
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Search filter for recipes."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'tags']


class IngredientFilter(filters.FilterSet):
    """
    Filter for aligning ingredients in order:
    first that start with searched phrase, then
    that contain it and then alphabetically.
    """

    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__istartswith=value) | Q(name__icontains=value)
        ).annotate(
            search_priority=Case(
                When(name__istartswith=value, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        ).order_by('search_priority', 'name')
