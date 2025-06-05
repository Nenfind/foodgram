from django.contrib import admin
from recipes.models import Recipe, Ingredient, Tag


admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tag)
