# Event API Image Upload Guide

## How to Upload Images to Event API

The Event API supports image uploads through multipart/form-data. Here are different ways to provide images:

## 1. Using Swagger UI (Recommended for Testing)

### Step 1: Access Swagger Documentation
1. Go to: `http://127.0.0.1:8000/api/docs/`
2. Find the Event endpoints under "Misc" section

### Step 2: Authenticate
1. Click "Authorize" button (🔒) at the top
2. Enter your admin token: `Bearer YOUR_TOKEN_HERE`
3. Example: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### Step 3: Create Event with Image
1. Expand `POST /misc/admin/events/` endpoint
2. Click "Try it out"
3. **IMPORTANT**: Change "Request body" dropdown to "multipart/form-data"
4. Fill in the form fields:
   ```
   title: "My New Event"
   description: "Event description"
   event_date: "2025-12-25"
   start_time: "10:00:00"
   end_time: "18:00:00"
   location: "Event Location"
   registration_link: "https://example.com/register"
   status: "PUBLISHED"
   is_featured: true
   original_image: [Choose File] <- Click to upload image
   ```
5. Click "Execute"

## 2. Using cURL Command

```bash
# Create event with image upload
curl -X POST "http://127.0.0.1:8000/api/misc/admin/events/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "title=Test Event with Image" \
  -F "description=This is a test event created with cURL" \
  -F "event_date=2025-12-31" \
  -F "start_time=18:00:00" \
  -F "end_time=23:59:00" \
  -F "location=Test Location" \
  -F "registration_link=https://test.com/register" \
  -F "status=PUBLISHED" \
  -F "is_featured=true" \
  -F "original_image=@/path/to/your/image.jpg"

# Update existing event (image optional)
curl -X PATCH "http://127.0.0.1:8000/api/misc/admin/events/1/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "title=Updated Event Title" \
  -F "location=Updated Location" \
  -F "original_image=@/path/to/new/image.jpg"
```

## 3. Using Python Requests

```python
import requests

# Your admin token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
headers = {"Authorization": f"Bearer {token}"}

# Create event with image
with open('/path/to/your/image.jpg', 'rb') as image_file:
    data = {
        'title': 'Python API Event',
        'description': 'Created using Python requests',
        'event_date': '2025-12-25',
        'start_time': '15:00:00',
        'end_time': '20:00:00',
        'location': 'Python Test Location',
        'registration_link': 'https://python-test.com/register',
        'status': 'PUBLISHED',
        'is_featured': True
    }
    files = {
        'original_image': image_file
    }
    
    response = requests.post(
        'http://127.0.0.1:8000/api/misc/admin/events/',
        data=data,
        files=files,
        headers=headers
    )
    
    if response.status_code == 201:
        event = response.json()
        print(f"Event created: {event['title']}")
        print(f"Image URLs:")
        print(f"- Thumbnail: {event['thumbnail_url']}")
        print(f"- Banner: {event['banner_url']}")
        print(f"- Original: {event['original_image_url']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
```

## 4. Using JavaScript/Fetch

```javascript
// Get your admin token first
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";

// Create FormData for file upload
const formData = new FormData();
formData.append('title', 'JavaScript Event');
formData.append('description', 'Created using JavaScript');
formData.append('event_date', '2025-12-31');
formData.append('start_time', '19:00:00');
formData.append('end_time', '23:59:00');
formData.append('location', 'JS Test Location');
formData.append('registration_link', 'https://js-test.com/register');
formData.append('status', 'PUBLISHED');
formData.append('is_featured', 'true');

// Add image file (from file input)
const fileInput = document.getElementById('imageFile');
formData.append('original_image', fileInput.files[0]);

// Make the request
fetch('http://127.0.0.1:8000/api/misc/admin/events/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
        // Don't set Content-Type - let browser set it for FormData
    },
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Event created:', data);
    console.log('Image URLs:', {
        thumbnail: data.thumbnail_url,
        banner: data.banner_url,
        original: data.original_image_url
    });
})
.catch(error => console.error('Error:', error));
```

## 5. Using Postman

### Step 1: Set up Request
1. Method: `POST`
2. URL: `http://127.0.0.1:8000/api/misc/admin/events/`

### Step 2: Add Authorization
1. Go to "Authorization" tab
2. Type: "Bearer Token"
3. Token: Your admin JWT token

### Step 3: Set up Body
1. Go to "Body" tab
2. Select "form-data" (NOT "raw" or "JSON")
3. Add fields:
   - Key: `title`, Value: `Postman Test Event`
   - Key: `description`, Value: `Created via Postman`
   - Key: `event_date`, Value: `2025-12-25`
   - Key: `start_time`, Value: `14:00:00`
   - Key: `end_time`, Value: `18:00:00`
   - Key: `location`, Value: `Postman Location`
   - Key: `status`, Value: `PUBLISHED`
   - Key: `is_featured`, Value: `true`
   - Key: `original_image`, Type: `File` (select your image file)

### Step 4: Send Request
Click "Send" and check the response for image URLs.

## Image Requirements

### Supported Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)

### Recommended Specifications
- **Minimum Size**: 800x600 pixels
- **Recommended Size**: 1200x800 pixels or higher
- **Aspect Ratio**: 3:2 or 4:3 for best results
- **File Size**: Under 10MB
- **Quality**: High resolution for best thumbnail/banner generation

### Image Processing
The system automatically generates:
1. **Thumbnail**: 400x300px (85% quality JPEG)
2. **Banner**: 1200x600px (90% quality JPEG) 
3. **Original**: Stored as uploaded

## Response Format

Successful creation returns:
```json
{
  "id": 4,
  "title": "Your Event Title",
  "slug": "your-event-title",
  "description": "Your description",
  "original_image": "/media/events/your_image.jpg",
  "thumbnail_url": "http://127.0.0.1:8000/media/CACHE/images/events/your_image_thumbnail.jpg",
  "banner_url": "http://127.0.0.1:8000/media/CACHE/images/events/your_image_banner.jpg",
  "original_image_url": "http://127.0.0.1:8000/media/events/your_image.jpg",
  "event_date": "2025-12-25",
  "start_time": "14:00:00",
  "end_time": "18:00:00",
  "location": "Your Location",
  "registration_link": "https://your-link.com",
  "status": "PUBLISHED",
  "is_featured": true,
  "days_until": 138,
  "created_at": "2025-08-09T22:45:12Z",
  "updated_at": "2025-08-09T22:45:12Z"
}
```

## Common Errors

### 1. Authentication Error (401)
```json
{"detail": "Authentication credentials were not provided."}
```
**Solution**: Include `Authorization: Bearer YOUR_TOKEN` header

### 2. Permission Error (403)
```json
{"detail": "You do not have permission to perform this action."}
```
**Solution**: Use admin account token

### 3. File Too Large (413)
```json
{"original_image": ["File too large. Maximum size is 10MB."]}
```
**Solution**: Compress image or use smaller file

### 4. Invalid Image Format (400)
```json
{"original_image": ["Upload a valid image file."]}
```
**Solution**: Use JPEG, PNG, or WebP format

### 5. Missing Required Fields (400)
```json
{
  "title": ["This field is required."],
  "event_date": ["This field is required."],
  "original_image": ["This field is required."]
}
```
**Solution**: Include all required fields

## Testing Your Implementation

1. **Get Admin Token**:
   ```bash
   curl -X POST "http://127.0.0.1:8000/api/auth/login/" \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@okpuja.com", "password": "admin@123"}'
   ```

2. **Test Image Upload** with the token received

3. **Verify Image URLs** in the response work correctly

4. **Check File System** that images are stored in `media/events/`

The API is ready for production use with proper image handling! 🎉
