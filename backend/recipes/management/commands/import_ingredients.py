from recipes.management.commands._base import BaseImportCommand
from recipes.models import Ingredient


class Command(BaseImportCommand):
    model = Ingredient
    filename = 'ingredients.json'
