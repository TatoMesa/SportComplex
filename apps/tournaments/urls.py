from django.urls import path
from . import views

app_name = "tournaments"

urlpatterns = [
    path("", views.TournamentSelectComplexView.as_view(), name="list"),
    path("<slug:slug>/", views.TournamentListView.as_view(), name="list"),
    path("<slug:slug>/nuevo/", views.TournamentCreateView.as_view(), name="create"),
    path("<slug:slug>/<uuid:pk>/", views.TournamentDetailView.as_view(), name="detail"),
    path("<slug:slug>/<uuid:pk>/categoria/", views.AddCategoryView.as_view(), name="add_category"),
    path("<slug:slug>/<uuid:pk>/categoria/<uuid:cat_pk>/equipo/", views.AddTeamView.as_view(), name="add_team"),
    path("<slug:slug>/<uuid:pk>/categoria/<uuid:cat_pk>/fixture/", views.GenerateFixtureView.as_view(), name="generate_fixture"),
    path("<slug:slug>/<uuid:pk>/partido/<uuid:match_pk>/resultado/", views.UpdateMatchResultView.as_view(), name="match_result"),
]