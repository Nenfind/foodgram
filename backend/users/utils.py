from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError


def validate_password_with_exception(
    password: str, field_name: str = "password"
) -> None:
    """
    Uses standard Django password validation,
    if validation fails raises serializer
    exception with field name message.
    """
    try:
        validate_password(password)
    except DjangoValidationError as e:
        raise serializers.ValidationError({field_name: e.messages})
