from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
import django.views.i18n as i18n_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('i18n/setlang/', i18n_views.set_language, name='set_language'),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('homepage.urls')),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)