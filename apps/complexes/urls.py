from django.urls import path
from . import views

app_name = "complexes"

urlpatterns = [
    path("", views.ComplexListView.as_view(), name="list"),
    path("nuevo/", views.ComplexCreateView.as_view(), name="create"),
    path("<slug:slug>/", views.ComplexDetailView.as_view(), name="detail"),
    path("<slug:slug>/editar/", views.ComplexUpdateView.as_view(), name="update"),
    path("<slug:slug>/canchas/nueva/", views.CourtCreateView.as_view(), name="court_create"),
]