import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from api.utils import get_user_from_context, is_recipe_in_relation
from core.constants import MIN_COOKING_TIME
from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, Tag
from shop.models import ShoppingCart
from users.models import Subscription
from users.utils import validate_password_with_exception

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
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = (
        'email', 'id', 'username', 'first_name',
        'last_name', 'is_subscribed', 'avatar', 'password'
        )
        required_fields = (
            'email', 'first_name',
            'last_name', 'password',
        )

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user and user.is_authenticated:
            return Subscription.objects.filter(
                user=user,
                subscription=obj,
            ).exists()
        return False

    def to_representation(self, instance):
        fields = super().to_representation(instance)
        request = self.context.get('request')
        if (
                request.method == 'POST'
                and request.path.endswith('/api/users/')
            ):
            fields.pop('is_subscribed', None)
            fields.pop('avatar', None)
        return fields

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        validate_password_with_exception(password, 'password')
        user.set_password(password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)
    current_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Введён неправильный пароль!'}
            )
        validate_password_with_exception(
            attrs['new_password'],
            'new_password'
        )
        return attrs


class AvatarForUserSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


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
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def create(self, validated_data):
        author = self.context['request'].user
        return Recipe.objects.create(**validated_data, author=author)

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_is_favorited(self, obj):
        user = get_user_from_context(self.context)
        return is_recipe_in_relation(obj, user, Favorite)

    def get_is_in_shopping_cart(self, obj):
        user = get_user_from_context(self.context)
        return is_recipe_in_relation(obj, user, ShoppingCart)


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
        validated_ingredients = []
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Должно быть положительное количество ингредиента!'
                )
            try:
                existing_ingredient = Ingredient.objects.get(id=ingredient['id'])
                if existing_ingredient in validated_ingredients:
                    raise serializers.ValidationError(
                        'Рецепт содержит дублирующиеся ингредиенты.'
                    )
                validated_ingredients.append(existing_ingredient)
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    'Данного ингредиента не существует.'
                )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один теги.'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Рецепт не должен содержать повторяющиеся теги.'
            )
        return tags

    def add_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
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
        try:
            ingredients_data = validated_data.pop('ingredients')
            tags_data = validated_data.pop('tags')
        except KeyError:
            raise serializers.ValidationError(
                'Заполните все нужные поля!'
            )
        ingredients_data = self.validate_ingredients(ingredients_data)
        tags_data = self.validate_tags(tags_data)
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()
        self.add_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = self.context[
            'request'
        ].build_absolute_uri(
            instance.image.url
        )

        return representation


class SubscriptionUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if request:
            try:
                limit = int(request.query_params.get('recipes_limit'))
                recipes = recipes[:limit]
            except (TypeError, ValueError):
                pass
        return RecipeMinifiedSerializer(recipes, many=True, context=self.context).data
