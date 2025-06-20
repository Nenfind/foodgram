from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = DefaultRouter()

router.register(
    'recipes',
    RecipeViewSet,
    basename='recipes'
)
router.register(
    'tags',
    TagViewSet,
    basename='tags'
)
router.register(
    'users',
    UserViewSet,
    basename='users'
)
router.register(
    'ingredients',
    IngredientViewSet,
    basename='ingredients'
)

urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.authtoken')),

    path('', include(router.urls)),
]
