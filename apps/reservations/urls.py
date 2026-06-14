from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

app_name = "reservations"

urlpatterns = [
    path("", login_required(TemplateView.as_view(template_name="coming_soon.html")), name="list"),
]