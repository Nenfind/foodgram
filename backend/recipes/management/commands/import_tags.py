from recipes.management.commands._base import BaseImportCommand
from recipes.models import Tag


class Command(BaseImportCommand):
    model = Tag
    filename = 'tags.json'
