from django.urls import path
from . import views

urlpatterns = [
    # Terms of Service
    path('terms/current/', views.CurrentTermsOfServiceView.as_view(), name='terms-current'),
    path('terms/', views.TermsOfServiceListView.as_view(), name='terms-list'),
    path('terms/create/', views.TermsOfServiceCreateView.as_view(), name='terms-create'),
    path('terms/<slug:slug>/', views.TermsOfServiceDetailView.as_view(), name='terms-detail'),
    
    # Privacy Policy
    path('privacy/current/', views.CurrentPrivacyPolicyView.as_view(), name='privacy-current'),
    path('privacy/', views.PrivacyPolicyListView.as_view(), name='privacy-list'),
    path('privacy/create/', views.PrivacyPolicyCreateView.as_view(), name='privacy-create'),
    path('privacy/<slug:slug>/', views.PrivacyPolicyDetailView.as_view(), name='privacy-detail'),
    
    # Cancellation & Refund Policy
    path('cancellation/current/', views.CurrentCancellationPolicyView.as_view(), name='cancellation-current'),
    path('cancellation/', views.CancellationPolicyListView.as_view(), name='cancellation-list'),
    path('cancellation/create/', views.CancellationPolicyCreateView.as_view(), name='cancellation-create'),
    path('cancellation/<slug:slug>/', views.CancellationPolicyDetailView.as_view(), name='cancellation-detail'),
    
    # User Consent
    path('consent/', views.UserConsentView.as_view(), name='user-consent'),
    path('consent/history/', views.UserConsentHistoryView.as_view(), name='user-consent-history'),
]