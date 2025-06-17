from django.contrib.auth import get_user_model
from django.db.models import (
    Case,
    Exists,
    IntegerField,
    OuterRef,
    Q,
    Value,
    When
)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.paginators import PageLimitPagination
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    AvatarForUserSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
    UserSerializer
)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.utils import create_shopping_list
from users.models import Subscription

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Viewset for all users endpoints."""

    queryset = User.objects.prefetch_related('subscriptions')
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination

    def get_permissions(self):
        """Allows to create and look up accounts for anonymous users."""
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(
        detail=False,
        methods=('get',),
    )
    def me(self, request):
        serializer = UserSerializer(
            self.request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put', 'delete',),
        url_path=r'me/avatar'
    )
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarForUserSerializer(
                instance=request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            return Response(
                {'avatar': user.avatar.url}, status=status.HTTP_200_OK
            )
        request.user.avatar.delete()
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
    )
    def subscribe(self, request, pk=None):
        try:
            target_user = get_object_or_404(User, pk=pk)
        except NotFound:
            return Response(
                {"detail": "Такого пользователя не существует."},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.method == 'POST':
            if request.user == target_user:
                return Response(
                    {"error": "Нельзя подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(
                    user=request.user, subscription=target_user
            ).exists():
                return Response(
                    {"error": "Вы уже подписаны."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(
                user=request.user, subscription=target_user
            )
            serializer = SubscriptionUserSerializer(
                target_user,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            subscription=target_user
        ).delete()
        if not deleted:
            return Response(
                {"error": "Такой подписки не существует."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
    )
    def subscriptions(self, request):
        subscribed_users = User.objects.filter(
            subscriptions__user=request.user
        ).prefetch_related('recipes')
        page = self.paginate_queryset(subscribed_users)
        serializer = SubscriptionUserSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset for all recipes endpoints."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsOwnerOrReadOnly, )
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def get_queryset(self):
        user = self.request.user
        return Recipe.objects.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user=user,
                    recipe=OuterRef('pk')
                )
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=user,
                    recipe=OuterRef('pk')
                )
            )
        ).select_related(
            'author'
        ).prefetch_related('tags', 'ingredients')

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        return Response({
            'short-link': recipe.get_short_link(request)
        })

    @action(
        detail=False,
        methods=['get'],
        url_path=r's/(?P<short_link>[a-km-zA-HJ-NP-Z2-9]+)',
        url_name='recipe-shortlink',
    )
    def follow_short_link(self, request, short_link=None):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return Response(RecipeSerializer(recipe).data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            if ShoppingCart.objects.filter(
                    recipe=recipe, user=self.request.user
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(recipe=recipe, user=self.request.user)
            return Response(
                status=status.HTTP_201_CREATED,
                data=serializer.data)
        deleted, _ = ShoppingCart.objects.filter(
            user=self.request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        shopping_list = create_shopping_list(user)
        filename = f"{user.username}'s_shopping_list.txt"
        response = HttpResponse(
            shopping_list, content_type='text/plain; charset=utf-8',
            headers={
                "Content-Disposition": (
                    f"attachment; filename*=UTF-8''{filename}"
                ),
                "Content-Length": len(shopping_list.encode("utf-8"))
            }
        )
        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(
                recipe=recipe,
                user=self.request.user
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            Favorite.objects.create(recipe=recipe, user=self.request.user)
            return Response(
                status=status.HTTP_201_CREATED,
                data=serializer.data
            )
        deleted, _ = Favorite.objects.filter(
            user=self.request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ingredients."""

    serializer_class = IngredientSerializer

    def get_queryset(self):
        search = self.request.query_params.get('name', '')
        queryset = Ingredient.objects.all()

        if search:
            queryset = queryset.filter(
                Q(name__istartswith=search) | Q(name__icontains=search)
            ).annotate(
                search_priority=Case(
                    When(name__istartswith=search, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            ).order_by('search_priority', 'name')
        return queryset
