from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("apps.dashboard.urls", namespace="dashboard")),
    path("complejos/", include("apps.complexes.urls", namespace="complexes")),
    path("reservas/", include("apps.reservations.urls", namespace="reservations")),
    path("buscar/", include("apps.search.urls", namespace="search")),
    path("productos/", include("apps.products.urls", namespace="products")),
    path("torneos/", include("apps.tournaments.urls", namespace="tournaments")),
    path("productos/", include("apps.products.urls", namespace="products")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)