from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("perfil/", views.ProfileView.as_view(), name="profile"),
    path("perfil/editar/", views.ProfileUpdateView.as_view(), name="profile_update"),
    path("mis-reservas/", views.MyReservationsView.as_view(), name="my_reservations"),
]