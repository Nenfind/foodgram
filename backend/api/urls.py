from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from api.views import RecipeViewSet, TagViewSet, UserViewSet

router_v1 = DefaultRouter()

router_v1.register(
    r'recipes',
    RecipeViewSet,
    basename='recipes'
)
router_v1.register(
    r'tags',
    TagViewSet,
    basename='tags'
)
router_v1.register(
    r'users',
    UserViewSet,
    basename='users'
)

urlpatterns = [
    # path('auth/token/login/', TokenObtainView.as_view(), name='token_obtain'),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),

]