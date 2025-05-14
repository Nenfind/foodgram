import base64

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from core.constants import MIN_COOKING_TIME
from recipes.models import Favorite, Recipe, RecipeIngredient, Tag
from users.models import Subscription

User = get_user_model()

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
        'email', 'id', 'username', 'first_name',
        'last_name', 'is_subscribed', 'avatar'
        )

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None
    #
    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user and user.is_authenticated:
            return Subscription.objects.filter(
                user=user,
                subscription=obj,
            ).exists()
        return True


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=user, recipe=obj
        ).exists()

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    image = Base64ImageField(required=True)
    ingredients = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        write_only=True
    )
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(
        required=True,
        min_value=MIN_COOKING_TIME,
    )

    class Meta:
        model = Recipe
        fields = (
            'name', 'image', 'text', 'cooking_time',
            'ingredients', 'tags'
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.'
            )
        ingredients_by_instance = [
            ingredient['id'] for ingredient in ingredients
        ]
        if len(set(ingredients_by_instance)) != len(ingredients):
            raise serializers.ValidationError(
                'Рецепт содержит дублирующиеся ингредиенты.'
            )
        return ingredients

    def add_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags_data)
        self.add_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if ingredients_data:
            instance.recipe_ingredients.all().delete()
            self.add_ingredients(instance, ingredients_data)

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data
