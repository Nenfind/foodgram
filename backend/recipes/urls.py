from django.urls import path

from recipes import views

urlpatterns = [
    path(
        's/<slug:short_link>',
        views.follow_short_link,
        name='recipe_short_link'
    ),
]
