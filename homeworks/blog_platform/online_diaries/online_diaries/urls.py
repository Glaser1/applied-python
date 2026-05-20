from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("posts.urls", namespace="posts")),
    path("users/", include("users.urls", namespace="users")),
    path("auth/", include("users.auth_urls", namespace="auth_users")),
    path("admin/", admin.site.urls),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
