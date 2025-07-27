from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.views import serve  # Add this
from django.views.decorators.cache import never_cache  # Add this

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('lessons.urls')),
]

# DEVELOPMENT ONLY - Add these lines
if settings.DEBUG:
    urlpatterns += [
        path('static/<path:path>', never_cache(serve)),
    ]