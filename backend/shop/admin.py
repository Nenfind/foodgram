from django.contrib import admin

from core.constants import EMPTY_VALUE_RU
from shop.models import ShoppingCart


class ShoppingCartAdmin(admin.ModelAdmin):
    model = ShoppingCart
    list_display = ('recipe', 'user')
    search_fields = ('recipe', 'user',)
    empty_value_display = EMPTY_VALUE_RU


admin.site.register(ShoppingCart, ShoppingCartAdmin)
