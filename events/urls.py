from django.urls import path
from . import views

urlpatterns = [
    # Public & Discovery
    path('', views.home, name='home'),
    path('event/<slug:slug>/', views.event_detail, name='event_detail'),
    path('event/<slug:slug>/register/', views.register_event, name='register_event'),
    path('event/<slug:slug>/ask/', views.ask_question, name='ask_question'),
    
    # Passes & Certificates
    path('pass/<uuid:token>/', views.ticket_pass, name='ticket_pass'),
    path('certificate/<uuid:token>/', views.certificate_view, name='certificate_view'),
    path('certificate/verify/<uuid:token>/', views.verify_certificate, name='verify_certificate'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    
    # Community & Team Finder
    path('team-finder/', views.team_finder, name='team_finder'),
    path('team-finder/connect/<int:post_id>/', views.team_connect, name='team_connect'),
    path('team-finder/request/<int:req_id>/<str:new_status>/', views.team_request_status, name='team_request_status'),
    
    # Coordinator Portal & Scanning
    path('coordinator/', views.coordinator_dashboard, name='coordinator_dashboard'),
    path('coordinator/create/', views.coordinator_create_event, name='coordinator_create_event'),
    path('coordinator/manage/<slug:slug>/', views.coordinator_manage_event, name='coordinator_manage_event'),
    path('coordinator/checkin/<int:reg_id>/', views.coordinator_toggle_checkin, name='coordinator_toggle_checkin'),
    path('coordinator/scanner/<slug:slug>/', views.coordinator_scanner, name='coordinator_scanner'),
    path('coordinator/export/<slug:slug>/', views.coordinator_export_attendees, name='coordinator_export_attendees'),
    
    # AJAX Scanner API
    path('api/scan-ticket/', views.api_scan_ticket, name='api_scan_ticket'),
    
    # Administrator Control & Database Diagnostics
    path('admin-portal/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/toggle-coordinator/<int:profile_id>/', views.admin_toggle_coordinator, name='admin_toggle_coordinator'),
    path('mongodb-status/', views.mongodb_status, name='mongodb_status'),
    
    # Authentication (Real Users)
    path('login/', views.auth_login, name='login'),
    path('register/', views.auth_register, name='register'),
    path('logout/', views.auth_logout, name='logout'),
]
