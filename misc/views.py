from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Event, JobOpening, ContactUs
from .serializers import (
    EventSerializer,
    JobOpeningSerializer,
    ContactUsSerializer,
    ContactUsCreateSerializer,
    ContactUsAdminSerializer
)
from accounts.permissions import IsAdminOrReadOnly
from core.tasks import send_contact_confirmation_email, send_contact_notification_email

class EventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'is_featured']
    
    def get_queryset(self):
        # Show upcoming events by default
        return Event.objects.filter(
            status='PUBLISHED',
            event_date__gte=timezone.now().date()
        ).order_by('event_date')
    
    def list(self, request, *args, **kwargs):
        # Allow showing past events with a query parameter
        show_past = request.query_params.get('show_past', 'false').lower() == 'true'
        
        queryset = self.get_queryset()
        if show_past:
            queryset = Event.objects.filter(
                status='PUBLISHED'
            ).order_by('-event_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class EventDetailView(generics.RetrieveAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

class FeaturedEventsView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Event.objects.filter(
            status='PUBLISHED',
            is_featured=True,
            event_date__gte=timezone.now().date()
        ).order_by('event_date')[:4]

class JobOpeningListView(generics.ListAPIView):
    serializer_class = JobOpeningSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['job_type', 'location', 'is_active']
    
    def get_queryset(self):
        return JobOpening.objects.filter(
            is_active=True,
            application_deadline__gte=timezone.now()
        ).order_by('application_deadline')

class JobOpeningDetailView(generics.RetrieveAPIView):
    queryset = JobOpening.objects.all()
    serializer_class = JobOpeningSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

class ActiveJobOpeningsView(generics.ListAPIView):
    serializer_class = JobOpeningSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return JobOpening.objects.filter(
            is_active=True,
            application_deadline__gte=timezone.now()
        ).order_by('application_deadline')[:5]

class ContactUsCreateView(generics.CreateAPIView):
    serializer_class = ContactUsCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        contact = serializer.save()
        
        # Send confirmation to user
        send_contact_confirmation_email.delay(contact.id)
        
        # Send notification to admin
        send_contact_notification_email.delay(contact.id)

class ContactUsListView(generics.ListAPIView):
    serializer_class = ContactUsAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'subject']
    
    def get_queryset(self):
        return ContactUs.objects.all().order_by('-created_at')

class ContactUsDetailView(generics.RetrieveUpdateAPIView):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_update(self, serializer):
        instance = self.get_object()
        new_status = serializer.validated_data.get('status')
        
        # Handle status changes
        if new_status == ContactUsStatus.REPLIED and instance.status != ContactUsStatus.REPLIED:
            instance.mark_as_replied()
        elif new_status == ContactUsStatus.CLOSED and instance.status != ContactUsStatus.CLOSED:
            instance.mark_as_closed()
        else:
            serializer.save()

class ContactUsStatusUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk, status):
        contact = get_object_or_404(ContactUs, pk=pk)
        
        if status == 'replied':
            contact.mark_as_replied()
            return Response({'status': 'marked as replied'})
        elif status == 'closed':
            contact.mark_as_closed()
            return Response({'status': 'marked as closed'})
        else:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )