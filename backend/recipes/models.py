import shortuuid
from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator, MinValueValidator
from django.db import models

from core.constants import (
    MAX_LENGTH_INGREDIENT,
    MAX_LENGTH_LONG,
    MAX_LENGTH_MEASURE,
    MAX_LENGTH_SHORT,
    MAX_LENGTH_STR,
    MAX_LENGTH_TEXT, MIN_COOKING_TIME, SHORT_LINK_LENGTH
)

User = get_user_model()

class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='название ингредиента',
        max_length=MAX_LENGTH_INGREDIENT,
        blank=False,
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        verbose_name='единица измерения',
        max_length=MAX_LENGTH_MEASURE,
        blank=False,
        help_text='Укажите единицу измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return self.name[:MAX_LENGTH_STR]


class Tag(models.Model):
    name = models.CharField(
        verbose_name='имя тега',
        max_length=MAX_LENGTH_SHORT,
        unique=True,
        help_text='Введите имя тега'
    )
    slug = models.SlugField(
        verbose_name='слаг',
        max_length=MAX_LENGTH_SHORT,
        unique=True,
        help_text='Введите слаг'
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'тэги'

    def __str__(self):
        return self.name[:MAX_LENGTH_STR]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes',
        blank=False
    )
    name = models.CharField(
        verbose_name='название рецепта',
        max_length=MAX_LENGTH_LONG,
        blank=False,
        help_text='Введите название рецепта'
    )
    image = models.ImageField(
        verbose_name='изображение блюда',
        blank=False,
        upload_to='recipe_images',
    )
    text = models.TextField(
        verbose_name='описание рецепта',
        validators=[MaxLengthValidator(MAX_LENGTH_TEXT)],
        blank=False,
        null=False,
        help_text='Опишите ваш рецепт'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='теги',
        related_name='recipes',
        blank=False,
        help_text='Добавьте теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='ингредиент',
        blank=False,
        related_name='recipes',
        through='RecipeIngredient',
        help_text='Добавьте необходимые ингредиенты'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления',
        blank=False,
        validators=[MinValueValidator(MIN_COOKING_TIME)],
        help_text='Введите время приготовления'
    )
    short_link = models.SlugField(
        verbose_name='короткая ссылка',
        max_length=MAX_LENGTH_LONG,
        unique=True,
        blank=True,
        help_text='Короткая неизменяющаяся ссылка',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return self.name[:MAX_LENGTH_STR]

    def save(self, *args, **kwargs):
        if not self.short_link:
            while True:
                self.short_link = shortuuid.ShortUUID().random(
                    length=SHORT_LINK_LENGTH
                )
                if not Recipe.objects.filter(short_link=self.short_link).exists():
                    break
        super().save(*args, **kwargs)

    def get_short_link(self, request):
        if request:
            return request.build_absolute_uri(f'/s/{self.short_link}/')
        return f'/s/{self.short_link}/'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='количество ингредиента',
        blank=False,
        null=False,
        help_text='Введите нужное количество'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            ),
        ]


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='пользователь'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='unique_favorite_recipe'
            )
        ]
