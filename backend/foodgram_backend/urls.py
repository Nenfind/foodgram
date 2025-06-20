from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('recipes.urls')),
]
if settings.DEBUG:
    urlpatterns += [
        static(
            settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
        ),
        path(
            'api/redoc/',
            TemplateView.as_view(template_name='redoc.html'),
            name='redoc'
        ),
    ]
