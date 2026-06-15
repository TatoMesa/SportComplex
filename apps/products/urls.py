from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.ProductSelectComplexView.as_view(), name="list"),
    path("<slug:slug>/", views.ProductListView.as_view(), name="complex_list"),
    path("<slug:slug>/nuevo/", views.ProductCreateView.as_view(), name="create"),
    path("<slug:slug>/<uuid:pk>/editar/", views.ProductUpdateView.as_view(), name="update"),
    path("<slug:slug>/<uuid:pk>/stock/", views.StockAdjustmentView.as_view(), name="stock"),
    path("<slug:slug>/ventas/", views.QuickSaleView.as_view(), name="quick_sale"),
]