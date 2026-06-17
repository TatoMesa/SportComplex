from django.urls import path
from . import views

app_name = "search"

urlpatterns = [
    path("", views.SearchView.as_view(), name="index"),
    path("favorito/<slug:slug>/", views.ToggleFavoriteView.as_view(), name="toggle_favorite"),
]