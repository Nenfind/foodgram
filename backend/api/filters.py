from django_filters import rest_framework as filters

from recipes.models import Favorite, Recipe, ShoppingCart, Tag


class RecipeFilter(filters.FilterSet):
    """Search filter for recipes."""

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
        fields = ['author', 'tags']

    def filter_by_relation(queryset, user, relation_model, value):
        """Filter recipes by relation"""
        if not value or user.is_anonymous:
            return queryset
        return queryset.filter(
            id__in=relation_model.objects.filter(user=user).values('recipe_id')
        )

    def filter_favorited(self, queryset, name, value):
        return self.filter_by_relation(queryset, self.request.user, Favorite, value)

    def filter_shopping_cart(self, queryset, name, value):
        return self.filter_by_relation(queryset, self.request.user, ShoppingCart, value)
