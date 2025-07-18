from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('packages/', views.packages, name='packages'),
    path('packages/<int:pk>/', views.package_detail, name='package_detail'),
    path('booking/', views.booking, name='booking'),
    path('quick-booking/', views.quick_booking, name='quick_booking'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('check-availability/', views.check_availability, name='check_availability'),
    path('process-payment/<int:booking_id>/', views.process_payment, name='process_payment'),
    
    # About and instructors
    path('about/', views.about, name='about'),
    path('instructors/<int:pk>/', views.instructor_detail, name='instructor_detail'),
    
    # FAQ system
    path('faq/', views.faq, name='faq'),
    path('comments/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    
    # Testimonials
    path('testimonials/', views.testimonials, name='testimonials'),
    
    # Contact and locations
    path('contact/', views.contact, name='contact'),
    
    # Legal pages
    path('legal/', views.legal, name='legal'),
    path('privacy/', views.privacy, name='privacy'),
    
    # Authentication and user accounts
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # API endpoints
    path('api/check-availability/', views.check_availability, name='api_check_availability'),
]

# Add error handlers
handler404 = 'lessons.views.handler404'
handler500 = 'lessons.views.handler500'