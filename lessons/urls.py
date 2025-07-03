from django.urls import path, include
from django.contrib.auth import views as auth_views  # این خط اضافه شد
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('packages/', views.packages, name='packages'),
    path('booking/', views.booking, name='booking'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Legal pages
    path('legal/', views.legal, name='legal'),
    path('privacy/', views.legal, name='privacy'),
    
    # FAQ system
    path('faq/', views.faq, name='faq'),
    path('comments/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    
    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),  # تغییر مسیر تمپلیت
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
]