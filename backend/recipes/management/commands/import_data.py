import json

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('model')
        parser.add_argument('file')

    def handle(self, *args, **options):
        Model = apps.get_model(options['model'])
        with open(options['file'], encoding='utf-8') as f:
            for item in json.load(f):
                Model.objects.get_or_create(**item)
