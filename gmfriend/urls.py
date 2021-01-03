from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from .views import Login, logout_then_login


urlpatterns = [
    path('login/', Login.as_view(), name='login'),
    path('logout/', logout_then_login, name='logout'),
    path('admin/', admin.site.urls),
    path('dnd5e/', include('dnd5e.urls', namespace='dnd5e')),
    path('markdownx/', include('markdownx.urls')),
]

if settings.DEBUG and settings.ENABLE_DEBUG_TOOLBAR:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns