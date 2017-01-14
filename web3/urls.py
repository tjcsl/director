"""web3 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings

from .apps.authentication import views as auth_views
from .apps.users import views as user_views

from .apps.error.views import (handle_404_view, handle_500_view, handle_503_view)

urlpatterns = [
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^$', auth_views.index_view, name='index'),
    url('^about$', auth_views.about_view, name='about'),
    url(r'^login/$', auth_views.login_view, name='login'),
    url(r'^login/superuser/$', auth_views.login_view, name='login_superuser'),
    url(r'^logout/$', auth_views.logout_view, name='logout'),
    url(r'^wsauth$', auth_views.node_auth_view, name='node_auth'),
    url(r"^user/", include("web3.apps.users.urls")),
    url(r"^site/", include("web3.apps.sites.urls")),
    url(r'^vm/', include("web3.apps.vms.urls")),
    url(r'^admin/', admin.site.urls),
    url(r'^github_oauth/$', user_views.github_oauth_view)
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

handler404 = handle_404_view
handler500 = handle_500_view
handler503 = handle_503_view
