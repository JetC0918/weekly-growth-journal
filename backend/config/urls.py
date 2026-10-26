from django.contrib import admin
from django.urls import include, path

from backend.accounts.views import LoginView, RegisterView
from backend.config.views import health


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="api-health"),
    path("api/auth/register", RegisterView.as_view(), name="api-auth-register"),
    path("api/auth/login", LoginView.as_view(), name="api-auth-login"),
    path("api/", include("backend.journal.urls")),
]
