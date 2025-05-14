from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model

class FoodgramUserCreationForm(UserCreationForm):
    model = User
    fields = (
        'email', 'first_name', 'last_name',
        'username', 'password'
    )
