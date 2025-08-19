# Event CRUD API Documentation

## Overview
This documentation describes the complete CRUD (Create, Read, Update, Delete) API for managing events in the OkPuja backend system. The API provides both public endpoints for viewing events and admin-only endpoints for managing events.

## Authentication & Permissions

### Admin Credentials
- **Email**: admin@okpuja.com
- **Password**: admin@123

### Permission Levels
- **Public Endpoints**: No authentication required (Read-only access to published events)
- **Admin Endpoints**: Admin authentication required (Full CRUD access)

## API Endpoints

### Public Endpoints

#### 1. List Public Events
- **URL**: `GET /api/misc/events/`
- **Permission**: Public (No authentication required)
- **Description**: Lists all published upcoming events
- **Query Parameters**:
  - `show_past=true`: Include past events
  - `status=PUBLISHED`: Filter by status
  - `is_featured=true`: Filter featured events only

**Example Request:**
```bash
curl -X GET "https://api.okpuja.com/api/misc/events/" \
  -H "accept: application/json"
```

**Example Response:**
```json
[
  {
    "id": 1,
    "title": "Maha Shivaratri Celebration 2025",
    "slug": "maha-shivaratri-celebration-2025",
    "description": "Join us for the grand celebration...",
    "thumbnail_url": "https://api.okpuja.com/media/events/thumbnails/event_1_sample.jpg",
    "banner_url": "https://api.okpuja.com/media/events/banners/event_1_sample.jpg",
    "original_image_url": "https://api.okpuja.com/media/events/event_1_sample.jpg",
    "event_date": "2025-09-08",
    "start_time": "06:00:00",
    "end_time": "23:59:00",
    "location": "Main Temple Hall, OkPuja Temple Complex",
    "registration_link": "https://okpuja.com/register/shivaratri-2025",
    "status": "PUBLISHED",
    "is_featured": true,
    "days_until": 30,
    "created_at": "2025-08-09T16:45:12Z",
    "updated_at": "2025-08-09T16:45:12Z"
  }
]
```

#### 2. Event Detail
- **URL**: `GET /api/misc/events/{slug}/`
- **Permission**: Public
- **Description**: Get detailed information about a specific event

**Example Request:**
```bash
curl -X GET "https://api.okpuja.com/api/misc/events/maha-shivaratri-celebration-2025/" \
  -H "accept: application/json"
```

#### 3. Featured Events
- **URL**: `GET /api/misc/events/featured/`
- **Permission**: Public
- **Description**: Get up to 4 featured upcoming events

### Admin Endpoints

#### 1. List All Events (Admin)
- **URL**: `GET /api/misc/admin/events/`
- **Permission**: Admin only
- **Description**: Lists all events (including drafts and archived)
- **Query Parameters**:
  - `status=DRAFT|PUBLISHED|ARCHIVED`: Filter by status
  - `is_featured=true|false`: Filter by featured status
  - `event_date=2025-09-08`: Filter by event date
  - `search=keyword`: Search in title, description, location
  - `ordering=event_date|-event_date|created_at|-created_at`: Sort results

**Example Request:**
```bash
curl -X GET "https://api.okpuja.com/api/misc/admin/events/" \
  -H "accept: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### 2. Create Event (Admin)
- **URL**: `POST /api/misc/admin/events/`
- **Permission**: Admin only
- **Content-Type**: `multipart/form-data` (for file upload)

**Required Fields:**
- `title`: Event title (max 255 characters)
- `event_date`: Event date (YYYY-MM-DD format)
- `original_image`: Image file (JPEG/PNG recommended)

**Optional Fields:**
- `description`: Event description (text)
- `start_time`: Start time (HH:MM:SS format)
- `end_time`: End time (HH:MM:SS format)
- `location`: Event location (max 255 characters)
- `registration_link`: Registration URL
- `status`: DRAFT|PUBLISHED|ARCHIVED (default: PUBLISHED)
- `is_featured`: true|false (default: false)

**Example Request:**
```bash
curl -X POST "https://api.okpuja.com/api/misc/admin/events/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "title=New Festival Event" \
  -F "description=A beautiful festival celebration" \
  -F "event_date=2025-10-15" \
  -F "start_time=10:00:00" \
  -F "end_time=18:00:00" \
  -F "location=Temple Complex" \
  -F "registration_link=https://okpuja.com/register" \
  -F "status=PUBLISHED" \
  -F "is_featured=true" \
  -F "original_image=@/path/to/your/image.jpg"
```

#### 3. Update Event (Admin)
- **URL**: `PATCH /api/misc/admin/events/{id}/`
- **Permission**: Admin only
- **Description**: Partially update an event

**Example Request:**
```bash
curl -X PATCH "https://api.okpuja.com/api/misc/admin/events/1/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Event Title",
    "location": "New Location",
    "is_featured": false
  }'
```

#### 4. Delete Event (Admin)
- **URL**: `DELETE /api/misc/admin/events/{id}/`
- **Permission**: Admin only

**Example Request:**
```bash
curl -X DELETE "https://api.okpuja.com/api/misc/admin/events/1/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### 5. Toggle Featured Status (Admin)
- **URL**: `POST /api/misc/admin/events/{id}/toggle-featured/`
- **Permission**: Admin only

**Example Request:**
```bash
curl -X POST "https://api.okpuja.com/api/misc/admin/events/1/toggle-featured/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### 6. Change Event Status (Admin)
- **URL**: `POST /api/misc/admin/events/{id}/change-status/`
- **Permission**: Admin only

**Example Request:**
```bash
curl -X POST "https://api.okpuja.com/api/misc/admin/events/1/change-status/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "ARCHIVED"}'
```

#### 7. Get Event Statistics (Admin)
- **URL**: `GET /api/misc/admin/events/stats/`
- **Permission**: Admin only

**Example Response:**
```json
{
  "total_events": 10,
  "published_events": 7,
  "draft_events": 2,
  "archived_events": 1,
  "featured_events": 3,
  "upcoming_events": 5
}
```

## Image Handling with ImageKit

### Image Upload Process
1. **Original Image**: Uploaded via the `original_image` field
2. **Automatic Processing**: ImageKit automatically generates:
   - **Thumbnail**: 400x300px (ResizeToFill, JPEG, 85% quality)
   - **Banner**: 1200x600px (ResizeToFit, JPEG, 90% quality)
3. **URL Generation**: All image URLs are automatically generated and included in API responses

### Image Specifications
- **Supported Formats**: JPEG, PNG, WebP
- **Recommended Size**: Minimum 1200x800px for best results
- **Maximum File Size**: 10MB (configurable)
- **Automatic Optimization**: Images are automatically optimized for web delivery

### Image URLs in Response
```json
{
  "thumbnail_url": "https://api.okpuja.com/media/CACHE/images/events/event_1/abc123_thumbnail.jpg",
  "banner_url": "https://api.okpuja.com/media/CACHE/images/events/event_1/abc123_banner.jpg",
  "original_image_url": "https://api.okpuja.com/media/events/event_1_original.jpg"
}
```

## Data Seeding & Testing

### 1. Seed Test Data
Run the management command to create sample events:

```bash
# Create sample events
python manage.py seed_events

# Clear existing and create new sample events
python manage.py seed_events --clear
```

### 2. Run Tests
Execute the comprehensive test suite:

```bash
# Run all misc app tests
python manage.py test misc

# Run with verbose output
python manage.py test misc --verbosity=2

# Run specific test class
python manage.py test misc.tests.EventAPITest
```

### 3. Test Coverage
The test suite covers:
- ✅ Model creation and validation
- ✅ Public API endpoints (anonymous access)
- ✅ Admin CRUD operations
- ✅ Permission restrictions
- ✅ Image upload and processing
- ✅ Search and filtering
- ✅ Status management
- ✅ Data validation
- ✅ Error handling

## Status Codes

### Success Codes
- `200 OK`: Successful GET, PATCH, POST (actions)
- `201 Created`: Successful POST (creation)
- `204 No Content`: Successful DELETE

### Error Codes
- `400 Bad Request`: Invalid data or validation errors
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Validation Rules

### Event Validation
1. **Title**: Required, max 255 characters, unique slug generated
2. **Event Date**: Cannot be in the past for new events
3. **Time Validation**: End time must be after start time
4. **Image**: Required for creation, supported formats only
5. **Status**: Must be one of DRAFT, PUBLISHED, ARCHIVED
6. **URL**: Registration link must be valid URL format

### Error Response Format
```json
{
  "field_name": ["Error message"],
  "non_field_errors": ["General error message"]
}
```

## Testing with Admin Credentials

### 1. Get Admin Token
```bash
curl -X POST "https://api.okpuja.com/api/accounts/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@okpuja.com",
    "password": "admin@123"
  }'
```

### 2. Use Token in Requests
```bash
curl -X GET "https://api.okpuja.com/api/misc/admin/events/" \
  -H "Authorization: Bearer YOUR_RECEIVED_TOKEN"
```

## Best Practices

### 1. Image Upload
- Use high-quality images (min 1200x800px)
- Compress images before upload to reduce file size
- Use descriptive filenames
- Test image URLs after upload

### 2. Event Management
- Create events in DRAFT status first
- Test all fields before publishing
- Use featured status sparingly for important events
- Archive old events instead of deleting

### 3. API Usage
- Always handle errors appropriately
- Use pagination for list endpoints
- Implement proper loading states in frontend
- Cache public endpoint responses when possible

## Troubleshooting

### Common Issues
1. **Image not displaying**: Check file permissions and MEDIA_ROOT settings
2. **403 Forbidden**: Verify admin token is valid and not expired
3. **Validation errors**: Check required fields and data formats
4. **Slug conflicts**: Titles must be unique or manually set different slugs

### Debug Commands
```bash
# Check event model
python manage.py shell -c "from misc.models import Event; print(Event.objects.all())"

# Verify admin permissions
python manage.py shell -c "from accounts.models import User; admin = User.objects.get(email='admin@okpuja.com'); print(admin.role, admin.account_status)"

# Test image processing
python manage.py shell -c "from misc.models import Event; e = Event.objects.first(); print(e.thumbnail.url if e.thumbnail else 'No thumbnail')"
```

This completes the comprehensive Event CRUD API with admin-only permissions, image handling via ImageKit, test data seeding, and thorough testing.
