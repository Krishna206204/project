
from django.urls import path
from . import views
urlpatterns = [
    path('',views.home,name='home'),
    path('about/' ,views.about,name="about"),
    path('contact/', views.contact,name="contact" ),
    path("login/selector", views.login_selection, name="login-selection"),
    path("login/", views.teacher_login, name="login"),
    path("accounts/logout/", views.teacher_logout, name="teacher-logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    
    
    
    path(
        "admin-login/",
        views.admin_login,
        name="admin-login"
    ),

    
    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin-dashboard"
    ),

    path(
        "logout/",
        views.admin_logout,
        name="admin-logout"
    ),
    
    path(
        "contact-messages/",
        views.admin_contact_messages,
        name="admin-contact-messages",
    ),
   
]