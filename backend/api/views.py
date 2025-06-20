from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import PageLimitPagination
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    AvatarForUserSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
    UserSerializer
)
from api.utils import create_shopping_list
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
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
        url_path='me/avatar'
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

    def get_user_for_subscription(self, id):
        try:
            target_user = get_object_or_404(User, pk=id)
        except NotFound:
            return Response(
                {"detail": "Такого пользователя не существует."},
                status=status.HTTP_404_NOT_FOUND
            )
        return target_user

    @action(
        detail=True,
        methods=['post'],
    )
    def subscribe(self, request, id=None):
        target_user = self.get_user_for_subscription(id)
        if request.user == target_user:
            return Response(
                {"error": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        _, created = Subscription.objects.get_or_create(
            user=request.user, subscription=target_user
        )
        serializer = SubscriptionUserSerializer(
            target_user,
            context={'request': request}
        )
        return (
            Response(
                serializer.data, status=status.HTTP_201_CREATED
            ) if created else Response(
                {"error": "Вы уже подписаны."},
                status=status.HTTP_400_BAD_REQUEST
            )
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        target_user = self.get_user_for_subscription(id)
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
        return RecipeReadSerializer

    def get_queryset(self):
        return Recipe.objects.with_favorites_and_cart(
            self.request.user
        ).select_related(
            'author'
        ).prefetch_related('tags', 'ingredients')

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        return Response({
            'short-link': recipe.get_short_link(request)
        })

    def favorite_shopping_cart_add(self, request, model, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(
            recipe=recipe,
            user=request.user
        )
        serializer = RecipeMinifiedSerializer(
            recipe, context={'request': request}
        )
        if not created:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def favorite_shopping_cart_delete(self, model, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = model.objects.filter(
            user=self.request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self.favorite_shopping_cart_add(
            request, Favorite, pk
        )

    @favorite.mapping.delete
    def favorite_delete(self, request, pk=None):
        return self.favorite_shopping_cart_delete(
            Favorite, pk
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self.favorite_shopping_cart_add(
            request, ShoppingCart, pk
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        return self.favorite_shopping_cart_delete(
            ShoppingCart, pk
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        shopping_list = create_shopping_list(user)
        filename = f"{user.username}'s_shopping_list.txt"
        return HttpResponse(
            shopping_list, content_type='text/plain; charset=utf-8',
            headers={
                "Content-Disposition": (
                    f"attachment; filename*=UTF-8''{filename}"
                ),
                "Content-Length": len(shopping_list.encode("utf-8"))
            }
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ingredients."""

    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    queryset = Ingredient.objects.all()
