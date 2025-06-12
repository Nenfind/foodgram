from django.contrib import admin

from recipes.models import Ingredient, Recipe, Tag


class RecipeAdmin(admin.ModelAdmin):
    model = Recipe
    list_display = (
        'author', 'name', 'image',
        'text', 'cooking_time', 'get_favorites_count'
    )
    list_filter = (
        'tags',
    )
    list_editable = (
        'cooking_time', 'name',
    )
    search_fields = (
        'author', 'name',
    )

    def get_favorites_count(self, obj):
        return obj.favorites.count()
    get_favorites_count.short_description = 'В избранном'


class IngredientAdmin(admin.ModelAdmin):
    model = Ingredient
    list_display = ('name', 'measurement_unit')
    list_editable = ('measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name', 'measurement_unit')


class TagAdmin(admin.ModelAdmin):
    model = Tag
    list_display = ('name', 'slug')
    list_editable = ('slug',)
    search_fields = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
