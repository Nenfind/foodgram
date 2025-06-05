def get_user_from_context(context_or_request):
    """Extracts user from either serializer context or filter request"""
    return getattr(context_or_request, 'user', None) or context_or_request.get('request').user

def is_recipe_in_relation(recipe, user, relation_model):
    """Check if recipe is in user's relation (favorites/shopping cart)"""
    if user.is_anonymous:
        return False
    return relation_model.objects.filter(user=user, recipe=recipe).exists()

def filter_by_relation(queryset, user, relation_model, value):
    """Filter recipes by relation"""
    if not value:
        return queryset
    if user.is_anonymous:
        return queryset.none()
    return queryset.filter(
        id__in=relation_model.objects.filter(user=user).values('recipe_id')
    )
