from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/new/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('assets/<int:pk>/checkout/', views.checkout, name='checkout'),
    path('assets/<int:pk>/checkin/', views.checkin, name='checkin'),
    path('assets/<int:pk>/move/', views.move_asset, name='move_asset'),
    path('assets/<int:pk>/attach/', views.attach_asset, name='attach_asset'),
    path('relationships/<int:rel_id>/detach/', views.detach_asset, name='detach_asset'),
    path('audit/', views.audit_log, name='audit_log'),
]
