import shortuuid
from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator
)
from django.db import models

from recipes.constants import (
    MAX_LENGTH_INGREDIENT,
    MAX_LENGTH_LONG,
    MAX_LENGTH_MEASURE,
    MAX_LENGTH_SHORT,
    MAX_LENGTH_STR,
    MAX_LENGTH_TEXT,
    MAX_POSITIVE_SMALL_INT,
    MIN_AMOUNT_OF_INGREDIENTS,
    MIN_COOKING_TIME,
    SHORT_LINK_LENGTH
)

User = get_user_model()


class Ingredient(models.Model):
    """
    Model for ingredients,
    contains name and measurement unit.
    """

    name = models.CharField(
        verbose_name='название ингредиента',
        max_length=MAX_LENGTH_INGREDIENT,
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        verbose_name='единица измерения',
        max_length=MAX_LENGTH_MEASURE,
        help_text='Укажите единицу измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_measurement_unit'
            )
        ]

    def __str__(self):
        return self.name[:MAX_LENGTH_STR]


class Tag(models.Model):
    """Model for tags, contains name and slug."""

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
    """Model for recipes, all fields are required."""

    author = models.ForeignKey(
        User,
        verbose_name='автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(
        verbose_name='название рецепта',
        max_length=MAX_LENGTH_LONG,
        help_text='Введите название рецепта'
    )
    image = models.ImageField(
        verbose_name='изображение блюда',
        upload_to='recipe_images',
    )
    text = models.TextField(
        verbose_name='описание рецепта',
        validators=[MaxLengthValidator(MAX_LENGTH_TEXT)],
        help_text='Опишите ваш рецепт'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='теги',
        related_name='recipes',
        help_text='Добавьте теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='ингредиент',
        related_name='recipes',
        through='RecipeIngredient',
        help_text='Добавьте необходимые ингредиенты'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_POSITIVE_SMALL_INT)
        ],
        help_text='Введите время приготовления'
    )
    short_link = models.SlugField(
        verbose_name='короткая ссылка',
        max_length=MAX_LENGTH_LONG,
        unique=True,
        blank=True,
        help_text='Короткая неизменяющаяся ссылка',
    )
    pub_date = models.DateTimeField(
        verbose_name='дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('pub_date', 'name',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return self.name[:MAX_LENGTH_STR]

    def save(self, *args, **kwargs):
        if not self.short_link:
            while True:
                self.short_link = shortuuid.ShortUUID().random(
                    length=SHORT_LINK_LENGTH
                ).lower()
                if not Recipe.objects.filter(
                        short_link=self.short_link
                ).exists():
                    break
        super().save(*args, **kwargs)

    def get_short_link(self, request):
        if request:
            return request.build_absolute_uri(f'/s/{self.short_link}/')
        return f'/s/{self.short_link}/'


class RecipeIngredient(models.Model):
    """Model for ingredients in recipes."""

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
        null=False,
        help_text='Введите нужное количество',
        validators=[
            MinValueValidator(MIN_AMOUNT_OF_INGREDIENTS),
            MaxValueValidator(MAX_POSITIVE_SMALL_INT)
        ],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            ),
        ]


class ShopFavorite(models.Model):
    """Abstract model for both shopping cart and favorites."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепты',
        related_name='%(app_label)s_%(model_name)s_related'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь',
        related_name='%(app_label)s_%(model_name)s_related'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='unique_%(app_label)s_%(class)s'
            )
        ]


class Favorite(ShopFavorite):
    """Model for favorites."""


class ShoppingCart(ShopFavorite):
    """Model for shopping cart."""

    class Meta(ShopFavorite.Meta):
        verbose_name = 'корзина покупок'
        verbose_name_plural = 'корзины покупок'
        default_related_name = 'shopping_cart'

    def __str__(self):
        return f'Корзина пользователя {self.user.username}'
