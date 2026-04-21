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
    path('portal/customer/<int:pk>/notifications/', views.customer_order_notifications, name='customer_order_notifications'),
    path('portal/staff/', views.staff_dashboard, name='staff_dashboard'),
    path('portal/staff/<int:pk>/', views.staff_order, name='staff_order'),
    path('portal/factory/', views.factory_dashboard, name='factory_dashboard'),
    path('portal/factory/<int:pk>/', views.factory_order, name='factory_order'),
    path('portal/staff/<int:pk>/quote/create/', views.staff_create_quote, name='staff_create_quote'),
    path('portal/staff/quote/<int:quote_pk>/', views.staff_quote_edit, name='staff_quote_edit'),
    path('portal/staff/quote/<int:quote_pk>/send/', views.staff_quote_send, name='staff_quote_send'),
    path('portal/staff/quote/<int:quote_pk>/print/', views.staff_quote_print, name='staff_quote_print'),
    path('portal/customer/<int:pk>/quote/', views.customer_quote_view, name='customer_quote_view'),
    path('portal/quote/<int:quote_pk>/sign/', views.quote_sign, name='quote_sign'),
    path('portal/staff/update/<int:update_pk>/delete/', views.staff_delete_update, name='staff_delete_update'),
]