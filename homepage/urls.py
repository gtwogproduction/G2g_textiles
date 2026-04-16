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
]