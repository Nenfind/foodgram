from django.contrib import admin
from django.db.models import Count

from recipes.constants import EMPTY_VALUE_RU
from recipes.models import Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    fields = ('ingredient', 'amount',)
    min_num = 1
    extra = 1
    validate_min = True
    autocomplete_fields = ['ingredient']


class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = (
        'author', 'name', 'image',
        'text', 'cooking_time', 'favorites_count',
    )
    list_filter = (
        'tags', 'author__username'
    )
    list_editable = (
        'cooking_time', 'name',
    )
    search_fields = (
        'author', 'name',
    )
    empty_value_display = EMPTY_VALUE_RU
    min_num = 1

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            favorites_count=Count('favorites'),
        )

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites_count



class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_editable = ('measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name', 'measurement_unit')
    empty_value_display = EMPTY_VALUE_RU


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_editable = ('slug',)
    search_fields = ('name',)
    empty_value_display = EMPTY_VALUE_RU


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')
    search_fields = ('recipe', 'user',)
    empty_value_display = EMPTY_VALUE_RU


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
