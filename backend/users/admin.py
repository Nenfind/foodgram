from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from recipes.constants import EMPTY_VALUE_RU

User = get_user_model()


class FoodgramUserAdmin(UserAdmin):
    model = User
    list_display = (
        'email',
        'first_name',
        'last_name',
        'username',
        'is_staff',
        'is_active',
    )
    list_editable = (
        'is_staff',
        'is_active',
    )
    search_fields = ('email', 'username')
    empty_value_display = EMPTY_VALUE_RU


admin.site.register(User, FoodgramUserAdmin)
admin.site.unregister(Group)
