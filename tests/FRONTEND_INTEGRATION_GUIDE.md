# 🌟 Frontend Integration Guide: Astrology Booking with Payment

## Next.js 15 + TypeScript Integration for OKPUJA Astrology Services

### 📋 Overview
This guide shows how to integrate the astrology booking system with payment processing in your Next.js 15 TypeScript project.

## 🛠️ Frontend Setup

### 1. Install Required Dependencies

```bash
npm install axios react-hook-form @hookform/resolvers zod
npm install @types/node @types/react @types/react-dom
npm install lucide-react # for icons
npm install react-toastify # for notifications
```

### 2. Create Type Definitions

Create `types/astrology.ts`:

```typescript
// types/astrology.ts
export interface AstrologyService {
  id: number;
  title: string;
  service_type: 'HOROSCOPE' | 'MATCHING' | 'PREDICTION' | 'REMEDIES' | 'GEMSTONE' | 'VAASTU';
  description: string;
  price: string;
  duration_minutes: number;
  is_active: boolean;
  image_url?: string;
  image_thumbnail_url?: string;
  image_card_url?: string;
}

export interface AstrologyBookingRequest {
  service: number;
  language: string;
  preferred_date: string; // YYYY-MM-DD
  preferred_time: string; // HH:MM:SS
  birth_place: string;
  birth_date: string; // YYYY-MM-DD
  birth_time: string; // HH:MM:SS
  gender: 'MALE' | 'FEMALE' | 'OTHER';
  questions?: string;
  contact_email: string;
  contact_phone: string;
  redirect_url: string;
}

export interface AstrologyBookingResponse {
  success: boolean;
  message: string;
  data: {
    booking: {
      id: number;
      service: AstrologyService;
      preferred_date: string;
      preferred_time: string;
      status: 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED';
    };
    payment: {
      payment_url: string;
      merchant_order_id: string;
      amount: number;
      amount_in_rupees: string;
    };
  };
}

export interface PaymentStatus {
  success: boolean;
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  merchant_order_id: string;
  booking_id?: number;
}
```

### 3. Create API Client

Create `lib/api.ts`:

```typescript
// lib/api.ts
import axios from 'axios';
import { AstrologyService, AstrologyBookingRequest, AstrologyBookingResponse } from '@/types/astrology';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = \`Bearer \${token}\`;
  }
  return config;
});

// API functions
export const astrologyAPI = {
  // Get all astrology services
  getServices: async (): Promise<AstrologyService[]> => {
    const response = await apiClient.get('/astrology/services/');
    return response.data;
  },

  // Get specific service
  getService: async (id: number): Promise<AstrologyService> => {
    const response = await apiClient.get(\`/astrology/services/\${id}/\`);
    return response.data;
  },

  // Create booking with payment
  createBookingWithPayment: async (
    bookingData: AstrologyBookingRequest
  ): Promise<AstrologyBookingResponse> => {
    const response = await apiClient.post('/astrology/bookings/book-with-payment/', bookingData);
    return response.data;
  },

  // Get user's bookings
  getUserBookings: async () => {
    const response = await apiClient.get('/astrology/bookings/');
    return response.data;
  }
};

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login/', {
      email,
      password
    });
    return response.data;
  },

  register: async (userData: any) => {
    const response = await apiClient.post('/auth/register/', userData);
    return response.data;
  }
};

export default apiClient;
```

### 4. Create Booking Form Component

Create `components/AstrologyBookingForm.tsx`:

```typescript
// components/AstrologyBookingForm.tsx
'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Calendar, Clock, MapPin, User, Phone, Mail, MessageSquare } from 'lucide-react';
import { toast } from 'react-toastify';
import { astrologyAPI } from '@/lib/api';
import { AstrologyService, AstrologyBookingRequest } from '@/types/astrology';

// Validation schema
const bookingSchema = z.object({
  language: z.string().min(1, 'Language is required'),
  preferred_date: z.string().min(1, 'Preferred date is required'),
  preferred_time: z.string().min(1, 'Preferred time is required'),
  birth_place: z.string().min(1, 'Birth place is required'),
  birth_date: z.string().min(1, 'Birth date is required'),
  birth_time: z.string().min(1, 'Birth time is required'),
  gender: z.enum(['MALE', 'FEMALE', 'OTHER']),
  questions: z.string().optional(),
  contact_email: z.string().email('Valid email is required'),
  contact_phone: z.string().min(10, 'Valid phone number is required'),
});

type BookingFormData = z.infer<typeof bookingSchema>;

interface Props {
  service: AstrologyService;
  onSuccess?: (bookingId: number) => void;
}

export default function AstrologyBookingForm({ service, onSuccess }: Props) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<BookingFormData>({
    resolver: zodResolver(bookingSchema),
  });

  const onSubmit = async (data: BookingFormData) => {
    setIsSubmitting(true);
    
    try {
      const bookingRequest: AstrologyBookingRequest = {
        service: service.id,
        ...data,
        redirect_url: \`\${window.location.origin}/payment-success\`
      };

      const response = await astrologyAPI.createBookingWithPayment(bookingRequest);
      
      if (response.success) {
        toast.success('Booking created successfully! Redirecting to payment...');
        
        // Redirect to PhonePe payment
        window.location.href = response.data.payment.payment_url;
        
        onSuccess?.(response.data.booking.id);
      }
    } catch (error: any) {
      console.error('Booking error:', error);
      toast.error(error.response?.data?.error || 'Failed to create booking');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Book {service.title}
        </h2>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>₹{service.price}</span>
          <span>•</span>
          <span>{service.duration_minutes} minutes</span>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Service Details */}
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-800 mb-2">Service Details</h3>
          <p className="text-blue-700 text-sm">{service.description}</p>
        </div>

        {/* Preferred Session */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Calendar size={16} />
              Preferred Date
            </label>
            <input
              type="date"
              {...register('preferred_date')}
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.preferred_date && (
              <p className="text-red-500 text-xs mt-1">{errors.preferred_date.message}</p>
            )}
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Clock size={16} />
              Preferred Time
            </label>
            <input
              type="time"
              {...register('preferred_time')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.preferred_time && (
              <p className="text-red-500 text-xs mt-1">{errors.preferred_time.message}</p>
            )}
          </div>
        </div>

        {/* Language */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Language
          </label>
          <select
            {...register('language')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select Language</option>
            <option value="Hindi">Hindi</option>
            <option value="English">English</option>
            <option value="Bengali">Bengali</option>
            <option value="Tamil">Tamil</option>
            <option value="Telugu">Telugu</option>
          </select>
          {errors.language && (
            <p className="text-red-500 text-xs mt-1">{errors.language.message}</p>
          )}
        </div>

        {/* Birth Details */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Birth Details</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <MapPin size={16} />
                Birth Place
              </label>
              <input
                type="text"
                {...register('birth_place')}
                placeholder="City, State, Country"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.birth_place && (
                <p className="text-red-500 text-xs mt-1">{errors.birth_place.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Birth Date
              </label>
              <input
                type="date"
                {...register('birth_date')}
                max={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.birth_date && (
                <p className="text-red-500 text-xs mt-1">{errors.birth_date.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Birth Time
              </label>
              <input
                type="time"
                {...register('birth_time')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.birth_time && (
                <p className="text-red-500 text-xs mt-1">{errors.birth_time.message}</p>
              )}
            </div>

            <div className="md:col-span-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <User size={16} />
                Gender
              </label>
              <select
                {...register('gender')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Gender</option>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
              {errors.gender && (
                <p className="text-red-500 text-xs mt-1">{errors.gender.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Contact Details */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Contact Details</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Mail size={16} />
                Email Address
              </label>
              <input
                type="email"
                {...register('contact_email')}
                placeholder="your@email.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.contact_email && (
                <p className="text-red-500 text-xs mt-1">{errors.contact_email.message}</p>
              )}
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Phone size={16} />
                Phone Number
              </label>
              <input
                type="tel"
                {...register('contact_phone')}
                placeholder="9876543210"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.contact_phone && (
                <p className="text-red-500 text-xs mt-1">{errors.contact_phone.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Questions */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <MessageSquare size={16} />
            Specific Questions (Optional)
          </label>
          <textarea
            {...register('questions')}
            rows={4}
            placeholder="Share any specific questions or areas you'd like to focus on during the consultation..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Submit Button */}
        <div className="pt-6 border-t">
          <button
            type="submit"
            disabled={isSubmitting}
            className={\`w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white py-3 px-6 rounded-md font-semibold transition-all duration-200 \${
              isSubmitting 
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:from-orange-600 hover:to-orange-700 transform hover:scale-[1.02]'
            }\`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Processing...
              </span>
            ) : (
              \`Pay ₹\${service.price} & Book Session\`
            )}
          </button>
          
          <p className="text-xs text-gray-500 text-center mt-2">
            You will be redirected to PhonePe for secure payment
          </p>
        </div>
      </form>
    </div>
  );
}
```

### 5. Create Service Selection Page

Create `app/astrology/page.tsx`:

```typescript
// app/astrology/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { astrologyAPI } from '@/lib/api';
import { AstrologyService } from '@/types/astrology';
import AstrologyBookingForm from '@/components/AstrologyBookingForm';

export default function AstrologyPage() {
  const [services, setServices] = useState<AstrologyService[]>([]);
  const [selectedService, setSelectedService] = useState<AstrologyService | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadServices();
  }, []);

  const loadServices = async () => {
    try {
      const data = await astrologyAPI.getServices();
      setServices(data);
    } catch (error) {
      console.error('Error loading services:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }

  if (selectedService) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="container mx-auto px-4">
          <button
            onClick={() => setSelectedService(null)}
            className="mb-6 text-orange-600 hover:text-orange-700 font-medium"
          >
            ← Back to Services
          </button>
          <AstrologyBookingForm service={selectedService} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            🔮 Astrology Services
          </h1>
          <p className="text-xl text-gray-600">
            Discover your path with personalized astrological insights
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service) => (
            <div
              key={service.id}
              className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
            >
              {service.image_card_url && (
                <img
                  src={service.image_card_url}
                  alt={service.title}
                  className="w-full h-48 object-cover"
                />
              )}
              <div className="p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-2">
                  {service.title}
                </h3>
                <p className="text-gray-600 mb-4 line-clamp-3">
                  {service.description}
                </p>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-2xl font-bold text-orange-600">
                    ₹{service.price}
                  </span>
                  <span className="text-sm text-gray-500">
                    {service.duration_minutes} min
                  </span>
                </div>
                <button
                  onClick={() => setSelectedService(service)}
                  className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white py-2 px-4 rounded-md font-semibold hover:from-orange-600 hover:to-orange-700 transition-all"
                >
                  Book Now
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 6. Create Payment Success Page

Create `app/payment-success/page.tsx`:

```typescript
// app/payment-success/page.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

export default function PaymentSuccessPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'failed'>('loading');

  useEffect(() => {
    // Get payment status from URL parameters
    const merchantOrderId = searchParams.get('merchantOrderId');
    const paymentStatus = searchParams.get('status');

    if (paymentStatus === 'SUCCESS') {
      setStatus('success');
    } else if (paymentStatus === 'FAILED') {
      setStatus('failed');
    } else {
      // Check payment status via API if needed
      setTimeout(() => setStatus('success'), 2000); // Simulate API call
    }
  }, [searchParams]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-orange-500 border-t-transparent mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-800">
            Verifying Payment...
          </h2>
          <p className="text-gray-600 mt-2">
            Please wait while we confirm your payment
          </p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-lg text-center max-w-md">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Booking Confirmed! 🎉
          </h2>
          <p className="text-gray-600 mb-6">
            Your astrology consultation has been booked successfully. 
            You will receive a confirmation email shortly.
          </p>
          <div className="space-y-3">
            <button
              onClick={() => window.location.href = '/astrology/bookings'}
              className="w-full bg-orange-500 text-white py-2 px-4 rounded-md hover:bg-orange-600 transition-colors"
            >
              View My Bookings
            </button>
            <button
              onClick={() => window.location.href = '/astrology'}
              className="w-full border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 transition-colors"
            >
              Book Another Session
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow-lg text-center max-w-md">
        <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Payment Failed
        </h2>
        <p className="text-gray-600 mb-6">
          Your payment could not be processed. Please try again.
        </p>
        <div className="space-y-3">
          <button
            onClick={() => window.location.href = '/astrology'}
            className="w-full bg-orange-500 text-white py-2 px-4 rounded-md hover:bg-orange-600 transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.href = '/contact'}
            className="w-full border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 transition-colors"
          >
            Contact Support
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 7. Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 8. Add Toast Notifications

In your `app/layout.tsx`:

```typescript
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </body>
    </html>
  );
}
```

## 🚀 Usage Flow

1. **User visits** `/astrology`
2. **Selects service** from the list
3. **Fills booking form** with personal and birth details
4. **Submits form** → API creates booking and returns PhonePe payment URL
5. **User redirected** to PhonePe for payment
6. **After payment** → User redirected to `/payment-success`
7. **Webhook confirms** payment → Booking status updated to CONFIRMED
8. **Email notifications** sent to both user and admin

## 📧 Email Flow

### User Emails:
- ✅ Booking confirmation with all details
- ✅ Professional HTML template
- ✅ Includes session information and next steps

### Admin Emails:
- ✅ New booking notification
- ✅ Customer details and requirements
- ✅ Direct link to admin panel

## 🔧 Backend API Endpoints Used

- `GET /api/astrology/services/` - List services
- `POST /api/astrology/bookings/book-with-payment/` - Create booking with payment
- `POST /api/payments/webhook/phonepe/` - Payment webhook (automatic)

Your frontend integration is now complete! The system handles the entire flow from service selection to payment confirmation with proper email notifications. 🎉
