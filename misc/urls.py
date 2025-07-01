from django.urls import path
from . import views

urlpatterns = [
    # Events
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/featured/', views.FeaturedEventsView.as_view(), name='featured-events'),
    path('events/<slug:slug>/', views.EventDetailView.as_view(), name='event-detail'),
    
    # Job Openings
    path('jobs/', views.JobOpeningListView.as_view(), name='job-list'),
    path('jobs/active/', views.ActiveJobOpeningsView.as_view(), name='active-jobs'),
    path('jobs/<slug:slug>/', views.JobOpeningDetailView.as_view(), name='job-detail'),
    
    # Contact Us
    path('contact/', views.ContactUsCreateView.as_view(), name='contact-create'),
    
    # Admin Endpoints
    path('admin/contact/', views.ContactUsListView.as_view(), name='admin-contact-list'),
    path('admin/contact/<int:pk>/', views.ContactUsDetailView.as_view(), name='admin-contact-detail'),
    path('admin/contact/<int:pk>/<str:status>/', views.ContactUsStatusUpdateView.as_view(), name='admin-contact-status'),
]