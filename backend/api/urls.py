from django.conf import settings
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router_v1 = DefaultRouter()

router_v1.register(
    'recipes',
    RecipeViewSet,
    basename='recipes'
)
router_v1.register(
    'tags',
    TagViewSet,
    basename='tags'
)
router_v1.register(
    'users',
    UserViewSet,
    basename='users'
)
router_v1.register(
    'ingredients',
    IngredientViewSet,
    basename='ingredients'
)

urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.authtoken')),

    path('', include(router_v1.urls)),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            'redoc/',
            TemplateView.as_view(template_name='redoc.html'),
            name='redoc'
        ),
    ]
