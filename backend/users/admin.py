from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

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
    empty_value_display = 'не задано'


admin.site.register(User, FoodgramUserAdmin)
