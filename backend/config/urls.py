from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from store import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('tracking/', views.tracking, name='tracking'),
    path('contact/', views.contact, name='contact'),
    path('api/products/', views.ProductList.as_view()),
    path('api/orders/', views.create_order),
    path('api/orders/<str:dedup_key>/', views.order_status),
    path('api/deep-link/<str:token>/', views.deep_link),
    path('api/custom-cake/', views.custom_cake),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
