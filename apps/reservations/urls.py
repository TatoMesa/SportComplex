from django.urls import path
from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.ReservationListView.as_view(), name="list"),
    path("nueva/", views.ReservationCreateView.as_view(), name="create"),
    path("nueva/<slug:slug>/", views.ReservationCreateView.as_view(), name="create_for_complex"),
    path("<uuid:pk>/", views.ReservationDetailView.as_view(), name="detail"),
    path("<uuid:pk>/cancelar/", views.ReservationCancelView.as_view(), name="cancel"),
    path("<uuid:pk>/pago/", views.ConfirmPaymentView.as_view(), name="confirm_payment"),
]