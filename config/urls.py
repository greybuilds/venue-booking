"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('web.urls')),
]

# dev only: look at every error page at /__errors/<400|403|404|500|csrf>/
from django.conf import settings
if settings.DEBUG:
    from web import views as _v
    urlpatterns += [
        path('__errors/400/', lambda r: _v.bad_request(r, None)),
        path('__errors/403/', lambda r: _v.forbidden(r, None)),
        path('__errors/404/', lambda r: _v.not_found(r, None)),
        path('__errors/500/', lambda r: _v.server_error(r)),
        path('__errors/csrf/', lambda r: _v.csrf_failure(r)),
    ]

handler404 = 'web.views.not_found'
handler403 = 'web.views.forbidden'
handler400 = 'web.views.bad_request'
handler500 = 'web.views.server_error'
