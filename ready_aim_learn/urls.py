from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.views import serve
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

def auth_debug(request):
    data = {
        'site': {
            'id': Site.objects.get_current().id,
            'domain': Site.objects.get_current().domain,
        },
        'google_app': list(SocialApp.objects.filter(provider='google').values()),
        'session': dict(request.session),
        'user': str(request.user),
    }
    return JsonResponse(data)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # For authentication
    path('auth-debug/', auth_debug),  # Debug endpoint
    path('', include('lessons.urls')),  # Your main app
]

# Development-only URLs
if settings.DEBUG:
    urlpatterns += [
        path('static/<path:path>', never_cache(serve)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)