from django.urls import path
from django.http import HttpResponse

app_name = "dashboard"

urlpatterns = [
    path("", lambda r: HttpResponse("Dashboard OK"), name="home"),
]