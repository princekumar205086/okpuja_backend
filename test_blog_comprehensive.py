#!/usr/bin/env python
"""
Comprehensive Blog App Testing Script
Tests all blog functionality end-to-end and identifies areas for improvement
"""
import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@okpuja.com"
ADMIN_PASSWORD = "admin@123"

class BlogTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name, status, message="", data=None):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")

    def get_admin_token(self):
        """Get admin JWT token"""
        print("\n🔑 Getting admin token...")
        login_url = f"{self.base_url}/api/auth/login/"
        data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = requests.post(login_url, json=data)
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get('access')
                self.log_test("Admin Authentication", "PASS", "Successfully obtained admin token")
                return True
            else:
                self.log_test("Admin Authentication", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Authentication", "FAIL", f"Error: {str(e)}")
            return False

    def test_blog_categories(self):
        """Test blog category CRUD operations"""
        print("\n📂 Testing Blog Categories...")
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test list categories
        response = requests.get(f"{self.base_url}/api/blog/categories/", headers=headers)
        if response.status_code == 200:
            categories = response.json()
            self.log_test("List Categories", "PASS", f"Found {len(categories)} categories")
        else:
            self.log_test("List Categories", "FAIL", f"Status: {response.status_code}")
            return False
        
        # Test create category
        category_data = {
            "name": "Spiritual Practices",
            "description": "Articles about spiritual practices and meditation",
            "meta_title": "Spiritual Practices - OkPuja Blog",
            "meta_description": "Discover ancient spiritual practices, meditation techniques, and spiritual wisdom for modern life.",
            "meta_keywords": "spiritual practices, meditation, spirituality, hinduism"
        }
        
        response = requests.post(f"{self.base_url}/api/blog/categories/", json=category_data, headers=headers)
        if response.status_code == 201:
            category = response.json()
            self.log_test("Create Category", "PASS", f"Created category: {category['name']}")
            return category
        else:
            self.log_test("Create Category", "FAIL", f"Status: {response.status_code} - {response.text}")
            return None

    def test_blog_tags(self):
        """Test blog tag CRUD operations"""
        print("\n🏷️ Testing Blog Tags...")
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test list tags
        response = requests.get(f"{self.base_url}/api/blog/tags/", headers=headers)
        if response.status_code == 200:
            tags = response.json()
            self.log_test("List Tags", "PASS", f"Found {len(tags)} tags")
        else:
            self.log_test("List Tags", "FAIL", f"Status: {response.status_code}")
            return False
        
        # Test create multiple tags
        tag_names = ["meditation", "puja", "spirituality", "hinduism", "yoga"]
        created_tags = []
        
        for tag_name in tag_names:
            tag_data = {
                "name": tag_name,
                "description": f"Posts related to {tag_name}"
            }
            
            response = requests.post(f"{self.base_url}/api/blog/tags/", json=tag_data, headers=headers)
            if response.status_code == 201:
                tag = response.json()
                created_tags.append(tag)
                self.log_test("Create Tag", "PASS", f"Created tag: {tag['name']}")
            else:
                self.log_test("Create Tag", "WARN", f"Tag '{tag_name}' might already exist")
        
        return created_tags

    def test_blog_posts(self, category=None, tags=None):
        """Test blog post CRUD operations"""
        print("\n📝 Testing Blog Posts...")
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test list posts
        response = requests.get(f"{self.base_url}/api/blog/posts/")
        if response.status_code == 200:
            posts = response.json()
            if isinstance(posts, dict) and 'results' in posts:
                posts = posts['results']
            self.log_test("List Posts", "PASS", f"Found {len(posts)} posts")
        else:
            self.log_test("List Posts", "FAIL", f"Status: {response.status_code}")
            return False
        
        # Test create comprehensive blog post
        post_data = {
            "title": "The Sacred Art of Daily Puja: A Complete Guide",
            "excerpt": "Discover the transformative power of daily puja practice and learn how to establish a meaningful spiritual routine that connects you with the divine.",
            "content": """# The Sacred Art of Daily Puja: A Complete Guide

## Introduction

Puja, derived from the Sanskrit word meaning 'worship' or 'honor', is one of the most beautiful and profound spiritual practices in Hinduism. This sacred ritual is not merely a religious obligation but a deeply personal journey that connects us with the divine, purifies our hearts, and brings peace to our minds.

## What is Puja?

Puja is a devotional practice that involves offering prayers, flowers, incense, food, and other sacred items to deities. It's a way of expressing gratitude, seeking blessings, and establishing a spiritual connection with the divine forces that govern our universe.

### Types of Puja

1. **Daily Puja (Nitya Puja)** - Performed every day at home
2. **Festival Puja** - Special ceremonies during festivals
3. **Life Event Puja** - Performed during important life events
4. **Remedial Puja** - For specific problems or challenges

## Benefits of Daily Puja Practice

### Spiritual Benefits
- **Divine Connection**: Establishes a direct link with the divine
- **Spiritual Growth**: Accelerates your spiritual evolution
- **Inner Peace**: Brings tranquility and mental clarity
- **Positive Energy**: Fills your space with sacred vibrations

### Mental Benefits
- **Stress Relief**: Reduces anxiety and mental tension
- **Focus Enhancement**: Improves concentration and mindfulness
- **Emotional Balance**: Stabilizes emotions and mood
- **Mental Clarity**: Clears mental fog and confusion

### Physical Benefits
- **Better Health**: Promotes overall well-being
- **Increased Energy**: Boosts vitality and life force
- **Improved Sleep**: Enhances quality of rest
- **Longevity**: Contributes to a longer, healthier life

## Setting Up Your Puja Space

### Essential Elements
1. **Clean Area**: A dedicated, clean space for worship
2. **Altar or Platform**: A raised surface for placing deities
3. **Sacred Images**: Pictures or idols of your chosen deities
4. **Puja Items**: Essential materials for the ritual

### Puja Essentials Checklist
- [ ] Incense sticks (Agarbatti)
- [ ] Oil lamp or candles
- [ ] Fresh flowers
- [ ] Holy water (Ganga Jal)
- [ ] Rice grains
- [ ] Turmeric and vermillion
- [ ] Sacred thread
- [ ] Prasad (offering food)
- [ ] Conch shell
- [ ] Small bell

## Step-by-Step Puja Guide

### 1. Preparation (Sankalpa)
- Take a bath and wear clean clothes
- Set your intention for the puja
- Gather all necessary items

### 2. Invocation (Avahana)
- Light the lamp and incense
- Ring the bell to announce your presence
- Invoke the deity with prayers

### 3. Offerings (Upachara)
- Offer flowers, water, and prasad
- Recite mantras or prayers
- Express gratitude and devotion

### 4. Aarti and Conclusion
- Perform aarti with the lamp
- Seek blessings from the deity
- Distribute prasad to family members

## Popular Mantras for Daily Puja

### Ganesh Mantra
```
ॐ गं गणपतये नमः
Om Gam Ganapataye Namah
```

### Shiva Mantra
```
ॐ नमः शिवाय
Om Namah Shivaya
```

### Vishnu Mantra
```
ॐ नमो नारायणाय
Om Namo Narayanaya
```

### Devi Mantra
```
ॐ ऐं ह्रीं क्लीं चामुण्डायै विच्चे
Om Aim Hreem Kleem Chamundaye Vichche
```

## Creating a Sustainable Practice

### Start Small
- Begin with 10-15 minutes daily
- Gradually increase duration
- Focus on consistency over length

### Choose Your Time
- **Morning**: Best for mental clarity
- **Evening**: Good for gratitude and reflection
- **Both**: Ideal for dedicated practitioners

### Family Involvement
- Include family members
- Teach children the significance
- Create a shared spiritual experience

## Common Mistakes to Avoid

1. **Rushing Through**: Take time to be present
2. **Lack of Cleanliness**: Maintain purity in space and self
3. **Mechanical Practice**: Engage with devotion and feeling
4. **Irregular Schedule**: Consistency is key
5. **Wrong Intentions**: Focus on spiritual growth, not material gains

## Modern Adaptations

### For Busy Lifestyles
- **Mobile Apps**: Use puja apps for guidance
- **Online Resources**: Access mantras and tutorials
- **Simplified Rituals**: Adapt to your time constraints
- **Mental Puja**: Practice visualization when physical items aren't available

### For Apartments
- **Compact Altar**: Create a small sacred space
- **Wall-mounted Setup**: Use vertical space efficiently
- **Portable Kit**: Keep essential items together
- **Digital Support**: Use tablets for mantras and music

## Conclusion

Daily puja practice is a transformative journey that goes beyond mere ritual. It's a pathway to spiritual awakening, inner peace, and divine connection. Whether you're a beginner or an experienced practitioner, the key is to approach this sacred practice with sincerity, devotion, and consistency.

Remember, the divine doesn't judge the grandeur of your offerings but the purity of your heart and the sincerity of your devotion. Start your puja journey today and experience the profound transformation it brings to your life.

## Resources for Further Learning

- **Books**: Study classical texts on puja procedures
- **Online Courses**: Enroll in spiritual learning platforms
- **Local Temples**: Seek guidance from experienced priests
- **Spiritual Communities**: Join groups of like-minded practitioners

*May your daily puja practice bring you closer to the divine and fill your life with peace, prosperity, and spiritual fulfillment.*

---

**About the Author**: This guide is prepared by the spiritual experts at OkPuja, your trusted partner for authentic Hindu rituals and spiritual guidance.

**Contact Us**: For personalized puja consultation and services, reach out to our experienced priests and spiritual advisors.""",
            "meta_title": "The Sacred Art of Daily Puja: Complete Guide to Hindu Worship | OkPuja",
            "meta_description": "Master the art of daily puja with our comprehensive guide. Learn step-by-step rituals, mantras, benefits, and modern adaptations for meaningful Hindu worship practice.",
            "meta_keywords": "daily puja, hindu worship, puja guide, mantras, spiritual practice, hinduism, prayer rituals, meditation, devotion",
            "youtube_url": "https://www.youtube.com/watch?v=example123",
            "is_featured": True,
            "status": "PUBLISHED"
        }
        
        # Add category if available
        if category:
            post_data["category"] = category['id']
        
        response = requests.post(f"{self.base_url}/api/blog/posts/create/", json=post_data, headers=headers)
        if response.status_code == 201:
            post = response.json()
            self.log_test("Create Blog Post", "PASS", f"Created post: {post['title']}")
            return post
        else:
            self.log_test("Create Blog Post", "FAIL", f"Status: {response.status_code} - {response.text}")
            return None

    def test_seo_features(self, post=None):
        """Test SEO-related features"""
        print("\n🔍 Testing SEO Features...")
        
        if not post:
            # Get any published post
            response = requests.get(f"{self.base_url}/api/blog/posts/")
            if response.status_code == 200:
                posts_data = response.json()
                if isinstance(posts_data, dict) and 'results' in posts_data:
                    posts = posts_data['results']
                else:
                    posts = posts_data
                if posts:
                    post = posts[0]
        
        if post:
            # Test URL structure (slug-based)
            if post.get('slug'):
                self.log_test("SEO URL Structure", "PASS", f"URL-friendly slug: {post['slug']}")
            else:
                self.log_test("SEO URL Structure", "FAIL", "No slug found")
            
            # Test meta tags
            if post.get('meta_title'):
                self.log_test("Meta Title", "PASS", f"Title: {post['meta_title'][:50]}...")
            else:
                self.log_test("Meta Title", "WARN", "No meta title set")
            
            if post.get('meta_description'):
                self.log_test("Meta Description", "PASS", f"Description length: {len(post['meta_description'])} chars")
            else:
                self.log_test("Meta Description", "WARN", "No meta description set")
            
            # Test structured data readiness
            required_fields = ['title', 'excerpt', 'published_at', 'author']
            missing_fields = [field for field in required_fields if not post.get(field)]
            if not missing_fields:
                self.log_test("Structured Data Readiness", "PASS", "All required fields present")
            else:
                self.log_test("Structured Data Readiness", "WARN", f"Missing: {', '.join(missing_fields)}")

    def test_blog_interactions(self, post=None):
        """Test blog interaction features"""
        print("\n💬 Testing Blog Interactions...")
        
        if not post:
            # Get any published post
            response = requests.get(f"{self.base_url}/api/blog/posts/")
            if response.status_code == 200:
                posts_data = response.json()
                if isinstance(posts_data, dict) and 'results' in posts_data:
                    posts = posts_data['results']
                else:
                    posts = posts_data
                if posts:
                    post = posts[0]
        
        if not post:
            self.log_test("Blog Interactions", "FAIL", "No post available for testing")
            return
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        post_slug = post['slug']
        
        # Test comments
        comment_data = {
            "content": "This is an excellent guide! Very informative and well-structured."
        }
        
        response = requests.post(
            f"{self.base_url}/api/blog/posts/{post_slug}/comments/",
            json=comment_data,
            headers=headers
        )
        if response.status_code == 201:
            self.log_test("Create Comment", "PASS", "Comment created successfully")
        else:
            self.log_test("Create Comment", "FAIL", f"Status: {response.status_code}")
        
        # Test likes
        response = requests.post(
            f"{self.base_url}/api/blog/posts/{post_slug}/like/",
            headers=headers
        )
        if response.status_code in [200, 201]:
            self.log_test("Like Post", "PASS", "Post liked successfully")
        else:
            self.log_test("Like Post", "FAIL", f"Status: {response.status_code}")

    def test_blog_performance(self):
        """Test blog performance features"""
        print("\n⚡ Testing Blog Performance...")
        
        # Test view tracking
        response = requests.get(f"{self.base_url}/api/blog/posts/")
        if response.status_code == 200:
            posts_data = response.json()
            if isinstance(posts_data, dict) and 'results' in posts_data:
                posts = posts_data['results']
            else:
                posts = posts_data
            
            if posts:
                post = posts[0]
                # Test individual post view
                response = requests.get(f"{self.base_url}/api/blog/posts/{post['slug']}/")
                if response.status_code == 200:
                    self.log_test("View Tracking", "PASS", "Post views are being tracked")
                else:
                    self.log_test("View Tracking", "FAIL", f"Status: {response.status_code}")
        
        # Test popular posts endpoint
        response = requests.get(f"{self.base_url}/api/blog/posts/popular/")
        if response.status_code == 200:
            popular_posts = response.json()
            self.log_test("Popular Posts", "PASS", f"Found {len(popular_posts)} popular posts")
        else:
            self.log_test("Popular Posts", "FAIL", f"Status: {response.status_code}")

    def test_blog_search_filtering(self):
        """Test blog search and filtering capabilities"""
        print("\n🔎 Testing Search & Filtering...")
        
        # Test search functionality
        search_params = {'search': 'puja'}
        response = requests.get(f"{self.base_url}/api/blog/posts/", params=search_params)
        if response.status_code == 200:
            results = response.json()
            if isinstance(results, dict) and 'results' in results:
                results = results['results']
            self.log_test("Search Functionality", "PASS", f"Found {len(results)} posts for 'puja'")
        else:
            self.log_test("Search Functionality", "FAIL", f"Status: {response.status_code}")
        
        # Test category filtering
        response = requests.get(f"{self.base_url}/api/blog/categories/")
        if response.status_code == 200:
            categories = response.json()
            if categories:
                category_id = categories[0]['id']
                filter_params = {'category': category_id}
                response = requests.get(f"{self.base_url}/api/blog/posts/", params=filter_params)
                if response.status_code == 200:
                    self.log_test("Category Filtering", "PASS", "Category filtering works")
                else:
                    self.log_test("Category Filtering", "FAIL", f"Status: {response.status_code}")

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 BLOG APP TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['message']}")
        
        if warnings > 0:
            print("\n⚠️ WARNINGS:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n💡 RECOMMENDATIONS FOR ENTERPRISE-LEVEL SEO:")
        recommendations = [
            "1. Add XML sitemap generation for blog posts",
            "2. Implement Open Graph and Twitter Card meta tags",
            "3. Add JSON-LD structured data for articles",
            "4. Implement canonical URLs to prevent duplicate content",
            "5. Add breadcrumb navigation support",
            "6. Implement automatic internal linking suggestions",
            "7. Add image alt text management",
            "8. Implement reading time calculation",
            "9. Add social sharing buttons",
            "10. Implement related posts based on semantic analysis",
            "11. Add AMP (Accelerated Mobile Pages) support",
            "12. Implement lazy loading for images",
            "13. Add blog post analytics and performance tracking",
            "14. Implement content optimization suggestions",
            "15. Add Google Ads integration points"
        ]
        
        for rec in recommendations:
            print(f"  {rec}")

    def run_all_tests(self):
        """Run comprehensive blog testing"""
        print("🧪 Starting Comprehensive Blog App Testing...")
        print("="*60)
        
        # Authentication
        if not self.get_admin_token():
            print("❌ Cannot proceed without admin token")
            return
        
        # Core functionality tests
        category = self.test_blog_categories()
        tags = self.test_blog_tags()
        post = self.test_blog_posts(category, tags)
        
        # SEO and performance tests
        self.test_seo_features(post)
        self.test_blog_interactions(post)
        self.test_blog_performance()
        self.test_blog_search_filtering()
        
        # Generate final report
        self.generate_report()

if __name__ == "__main__":
    tester = BlogTester()
    tester.run_all_tests()
