from django.shortcuts import redirect

from recipes.models import Recipe


def follow_short_link(self, request, short_link=None):
    try:
        recipe = Recipe.objects.get(short_link__iexact=short_link)
        return redirect(f'api/recipes/{recipe.pk}/')
    except Recipe.DoesNotExist:
        return redirect('/404/', permanent=False)
