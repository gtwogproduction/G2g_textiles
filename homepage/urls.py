from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('contact/', views.contact, name='contact'),
    path('quote/', views.quote, name='quote', kwargs={'step': 1}),
    path('quote/<int:step>/', views.quote, name='quote_step'),
    path('quote/success/', views.quote_success, name='quote_success'),
    path('impressum/', views.legal_page, name='impressum', kwargs={'page': 'impressum'}),
    path('agb/', views.legal_page, name='agb', kwargs={'page': 'agb'}),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    # Portal
    path('portal/login/', views.portal_login, name='portal_login'),
    path('portal/logout/', views.portal_logout, name='portal_logout'),
    path('portal/', views.portal_home, name='portal_home'),
    path('portal/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('portal/customer/<int:pk>/', views.customer_order, name='customer_order'),
    path('portal/staff/', views.staff_dashboard, name='staff_dashboard'),
    path('portal/staff/<int:pk>/', views.staff_order, name='staff_order'),
    path('portal/factory/', views.factory_dashboard, name='factory_dashboard'),
    path('portal/factory/<int:pk>/', views.factory_order, name='factory_order'),
]