import json

from django.conf import settings
from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    model = None
    filename = None

    def handle(self, *args, **options):
        file_path = settings.BASE_DIR / 'data' / self.filename
        model = self.model

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)
            objects = [model(**item) for item in data]
            model.objects.bulk_create(objects, ignore_conflicts=True)
