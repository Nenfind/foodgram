from rest_framework import viewsets
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin
)

class ListRetrieveViewSet(RetrieveModelMixin, ListModelMixin, viewsets.A):