# CORS Configuration Guide for OkPuja Frontend

This document provides instructions for configuring CORS (Cross-Origin Resource Sharing) in your frontend NextJS application to correctly interact with the OkPuja API.

## Backend CORS Changes

We've already made these changes on the backend:

1. Fixed CORS configuration in `settings.py`
2. Properly positioned the CORS middleware
3. Added additional CORS headers to allow credentials and specific request headers

## Frontend Configuration

To make your frontend work correctly with the API, you need to:

### 1. Use consistent API calls with CORS headers

```javascript
// Example API call with proper CORS headers
async function fetchServices() {
  try {
    const response = await fetch('https://api.okpuja.com/api/puja/services/', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Include any auth tokens if needed
      },
      credentials: 'include', // Include cookies if using session auth
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching services:', error);
    throw error;
  }
}
```

### 2. If using Axios, configure it properly:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.okpuja.com/api',
  withCredentials: true, // Include cookies if using session auth
  headers: {
    'Content-Type': 'application/json',
  }
});

// Example usage
async function fetchServices() {
  try {
    const response = await api.get('/puja/services/');
    return response.data;
  } catch (error) {
    console.error('Error fetching services:', error);
    throw error;
  }
}
```

### 3. In Next.js, you can configure CORS in `next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://api.okpuja.com/api/:path*',
      },
    ];
  },
  // If you're using Next.js API routes, you can add this:
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: 'https://api.okpuja.com' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,DELETE,PATCH,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
```

## Troubleshooting

If you still see CORS errors after these changes:

1. **Check the Network Tab**: Look at the response headers to ensure `Access-Control-Allow-Origin` is present
2. **Clear Browser Cache**: CORS errors can sometimes persist due to cached responses
3. **Check for Mixed HTTP/HTTPS**: Ensure you're not mixing HTTP and HTTPS in your requests
4. **Use Browser Extensions**: For development, you can use CORS extensions (but don't rely on them for production)

## Production Checklist

Before deploying to production:

1. Ensure all domains are listed in the backend's `CORS_ALLOWED_ORIGINS`
2. Test the API calls from the actual production domain
3. Remove any CORS browser extensions used during development
4. Ensure the API handles OPTIONS requests correctly (pre-flight requests)

By following these guidelines, your frontend should be able to successfully communicate with the OkPuja API without CORS errors.
