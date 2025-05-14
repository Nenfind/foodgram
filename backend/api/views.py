from django.contrib.auth import get_user_model, login
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken

from api.serializers import RecipeSerializer, TagSerializer, UserSerializer
from recipes.models import Recipe, Tag
from users.models import Subscription

User = get_user_model()

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = 'GET', 'POST', 'PATCH', 'DELETE'


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related('subscriptions')
    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        serializer = UserSerializer(
            self.request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,)
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
            Subscription.objects.create(user=request.user, subscription=target_user)
            serializer = UserSerializer(target_user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
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
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        subscribed_users = User.objects.filter(
            subscriptions__user=request.user
        ).prefetch_related('recipes')
        page = self.paginate_queryset(subscribed_users)
        serializer = UserSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)