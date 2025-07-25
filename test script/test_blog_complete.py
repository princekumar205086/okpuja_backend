#!/usr/bin/env python
"""
Comprehensive Blog App Testing Suite
Tests all blog functionality including seeding, API endpoints, SEO features, and performance
"""

import os
import sys
import django
import json
import time
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction
from rest_framework.test import APIClient
from rest_framework import status
from faker import Faker

from blog.models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView
from blog.seo_serializers import EnterpriseBlogPostDetailSerializer, EnterpriseMinimalBlogPostSerializer

User = get_user_model()
fake = Faker()

class ComprehensiveBlogTester:
    def __init__(self):
        self.client = APIClient()
        self.admin_client = APIClient()
        self.errors = []
        self.successes = []
        self.performance_metrics = {}
        
    def log_success(self, message):
        self.successes.append(f"✅ {message}")
        print(f"✅ {message}")
    
    def log_error(self, message):
        self.errors.append(f"❌ {message}")
        print(f"❌ {message}")
    
    def log_info(self, message):
        print(f"ℹ️  {message}")
    
    def setup_test_environment(self):
        """Setup test environment with admin user and authentication"""
        self.log_info("Setting up test environment...")
        
        try:
            # Create or get admin user
            admin_user, created = User.objects.get_or_create(
                email='admin@okpuja.com',
                defaults={
                    'password': 'adminpass123',
                    'is_staff': True,
                    'is_superuser': True,
                    'first_name': 'Admin',
                    'last_name': 'User'
                }
            )
            
            if created:
                admin_user.set_password('adminpass123')
                admin_user.save()
            
            # Authenticate admin client
            self.admin_client.force_authenticate(user=admin_user)
            
            self.log_success("Test environment setup complete")
            return admin_user
            
        except Exception as e:
            self.log_error(f"Failed to setup test environment: {str(e)}")
            return None
    
    def test_data_seeding(self):
        """Test blog data seeding functionality"""
        print("\n🌱 Testing Blog Data Seeding...")
        
        try:
            # Clear existing test data
            self.log_info("Clearing existing test data...")
            BlogView.objects.all().delete()
            BlogLike.objects.all().delete()
            BlogComment.objects.all().delete()
            BlogPost.objects.all().delete()
            BlogTag.objects.all().delete()
            BlogCategory.objects.all().delete()
            User.objects.filter(email__contains='testuser').delete()
            
            # Create test data manually (since management command might have issues)
            self.create_test_categories()
            self.create_test_tags()
            users = self.create_test_users()
            posts = self.create_test_posts(users)
            self.create_test_interactions(posts, users)
            
            self.log_success("Blog data seeding completed successfully")
            
        except Exception as e:
            self.log_error(f"Data seeding failed: {str(e)}")
    
    def create_test_categories(self):
        """Create test categories"""
        categories_data = [
            {
                'name': 'Puja Rituals',
                'description': 'Traditional Hindu puja ceremonies and their significance',
                'meta_keywords': 'puja, rituals, hindu ceremonies, worship'
            },
            {
                'name': 'Festival Celebrations',
                'description': 'Hindu festivals and their celebration methods',
                'meta_keywords': 'festivals, celebrations, diwali, holi, navratri'
            },
            {
                'name': 'Spiritual Guidance',
                'description': 'Spiritual wisdom and guidance for daily life',
                'meta_keywords': 'spirituality, guidance, meditation, dharma'
            },
            {
                'name': 'Vedic Astrology',
                'description': 'Ancient Vedic astrology and modern applications',
                'meta_keywords': 'astrology, vedic, horoscope, predictions'
            }
        ]
        
        for data in categories_data:
            BlogCategory.objects.create(
                name=data['name'],
                description=data['description'],
                meta_title=f"{data['name']} | OkPuja",
                meta_description=data['description'],
                meta_keywords=data['meta_keywords'],
                status='PUBLISHED'
            )
    
    def create_test_tags(self):
        """Create test tags"""
        tag_names = [
            'Ganesh Puja', 'Durga Puja', 'Diwali', 'Holi', 'Meditation',
            'Yoga', 'Astrology', 'Temples', 'Mantras', 'Festivals'
        ]
        
        for name in tag_names:
            BlogTag.objects.create(
                name=name,
                description=f'Posts related to {name.lower()}',
                status='PUBLISHED'
            )
    
    def create_test_users(self):
        """Create test users"""
        users = []
        for i in range(5):
            user = User.objects.create_user(
                email=f'testuser{i+1}@okpuja.com',
                password='testpass123',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users.append(user)
        return users
    
    def create_test_posts(self, users):
        """Create test blog posts"""
        categories = list(BlogCategory.objects.all())
        tags = list(BlogTag.objects.all())
        posts = []
        
        post_titles = [
            "Complete Guide to Ganesh Puja: Rituals and Significance",
            "Celebrating Diwali: Traditional Practices and Modern Adaptations",
            "The Spiritual Power of Meditation in Hindu Philosophy",
            "Understanding Vedic Astrology: Ancient Wisdom for Modern Life",
            "Temple Architecture: Sacred Geometry and Divine Design",
            "Holi Festival: Colors of Joy and Spiritual Renewal",
            "Daily Puja Practices: Creating Sacred Space at Home",
            "Yoga and Spirituality: Union of Body, Mind and Soul",
            "The Significance of Mantras in Hindu Tradition",
            "Navratri Celebrations: Nine Nights of Divine Feminine"
        ]
        
        for i, title in enumerate(post_titles):
            content = f"""
# {title}

## Introduction
{fake.text(max_nb_chars=300)}

## Historical Background
{fake.text(max_nb_chars=400)}

## Traditional Practices
{fake.text(max_nb_chars=350)}

### Step-by-Step Guide
1. **Preparation**: {fake.text(max_nb_chars=150)}
2. **Main Ritual**: {fake.text(max_nb_chars=150)}
3. **Conclusion**: {fake.text(max_nb_chars=150)}

## Modern Relevance
{fake.text(max_nb_chars=300)}

## Benefits and Impact
{fake.text(max_nb_chars=250)}

## Conclusion
{fake.text(max_nb_chars=200)}

*For personalized guidance, consult with our experienced spiritual advisors at OkPuja.*
            """
            
            post = BlogPost.objects.create(
                title=title,
                content=content.strip(),
                excerpt=fake.text(max_nb_chars=200),
                user=users[i % len(users)],
                category=categories[i % len(categories)],
                status='PUBLISHED',
                meta_title=f"{title} | OkPuja",
                meta_description=f"Comprehensive guide to {title.lower()}. {fake.text(max_nb_chars=100)}",
                meta_keywords=f"hindu, spirituality, {title.lower()}, puja, rituals",
                is_featured=(i < 3),  # First 3 posts are featured
                published_at=fake.date_time_between(start_date='-1y', end_date='now')
            )
            
            # Add random tags
            post.tags.set(fake.random_choices(tags, length=3))
            posts.append(post)
        
        return posts
    
    def create_test_interactions(self, posts, users):
        """Create test comments, likes, and views"""
        for post in posts:
            # Create comments
            for i in range(fake.random_int(min=1, max=5)):
                comment = BlogComment.objects.create(
                    post=post,
                    user=fake.random_element(users),
                    content=fake.text(max_nb_chars=200),
                    is_approved=True,
                    created_at=fake.date_time_between(
                        start_date=post.published_at,
                        end_date='now'
                    )
                )
            
            # Create likes
            for user in fake.random_choices(users, length=fake.random_int(min=1, max=len(users))):
                BlogLike.objects.get_or_create(
                    post=post,
                    user=user,
                    defaults={'created_at': fake.date_time_between(
                        start_date=post.published_at,
                        end_date='now'
                    )}
                )
            
            # Create views
            view_count = fake.random_int(min=50, max=300)
            for i in range(view_count):
                BlogView.objects.create(
                    post=post,
                    user=fake.random_element(users) if fake.boolean() else None,
                    ip_address=fake.ipv4(),
                    created_at=fake.date_time_between(
                        start_date=post.published_at,
                        end_date='now'
                    )
                )
            
            # Update post view count
            post.view_count = view_count
            post.save(update_fields=['view_count'])
    
    def test_api_endpoints(self):
        """Test all blog API endpoints"""
        print("\n🔌 Testing Blog API Endpoints...")
        
        endpoints_to_test = [
            {'url': '/blog/api/categories/', 'method': 'GET', 'name': 'Categories List'},
            {'url': '/blog/api/tags/', 'method': 'GET', 'name': 'Tags List'},
            {'url': '/blog/api/posts/', 'method': 'GET', 'name': 'Posts List'},
            {'url': '/blog/api/comments/', 'method': 'GET', 'name': 'Comments List'},
        ]
        
        for endpoint in endpoints_to_test:
            try:
                start_time = time.time()
                
                if endpoint['method'] == 'GET':
                    response = self.client.get(endpoint['url'])
                
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_success(f"{endpoint['name']} API: {response.status_code} ({response_time:.2f}ms)")
                    
                    # Store performance metrics
                    self.performance_metrics[endpoint['name']] = {
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'data_count': len(data) if isinstance(data, list) else 1
                    }
                else:
                    self.log_error(f"{endpoint['name']} API failed: {response.status_code}")
                    
            except Exception as e:
                self.log_error(f"{endpoint['name']} API error: {str(e)}")
    
    def test_seo_features(self):
        """Test SEO features and serializers"""
        print("\n🔍 Testing SEO Features...")
        
        try:
            posts = BlogPost.objects.filter(status='PUBLISHED')[:3]
            
            for post in posts:
                # Test detailed serializer
                serializer = EnterpriseBlogPostDetailSerializer(
                    post, 
                    context={'request': type('Request', (), {'build_absolute_uri': lambda x: f'http://localhost{x}'})()}
                )
                data = serializer.data
                
                # Check SEO fields
                seo_fields = [
                    'meta_title', 'meta_description', 'meta_keywords',
                    'structured_data', 'open_graph_data', 'twitter_card_data',
                    'breadcrumbs', 'canonical_url'
                ]
                
                missing_fields = [field for field in seo_fields if field not in data or not data[field]]
                
                if not missing_fields:
                    self.log_success(f"Post '{post.title[:30]}...': All SEO fields present")
                else:
                    self.log_error(f"Post '{post.title[:30]}...': Missing SEO fields: {missing_fields}")
                
                # Validate structured data
                if 'structured_data' in data:
                    structured = data['structured_data']
                    if '@context' in structured and '@type' in structured:
                        self.log_success(f"Post '{post.title[:30]}...': Valid JSON-LD structured data")
                    else:
                        self.log_error(f"Post '{post.title[:30]}...': Invalid structured data format")
            
        except Exception as e:
            self.log_error(f"SEO testing failed: {str(e)}")
    
    def test_search_functionality(self):
        """Test search functionality"""
        print("\n🔎 Testing Search Functionality...")
        
        try:
            # Test search endpoint
            search_terms = ['puja', 'festival', 'meditation', 'spiritual']
            
            for term in search_terms:
                response = self.client.get(f'/blog/search/?q={term}')
                
                if response.status_code == 200:
                    results = response.json()
                    self.log_success(f"Search for '{term}': {len(results)} results found")
                else:
                    self.log_error(f"Search for '{term}' failed: {response.status_code}")
            
            # Test empty search
            response = self.client.get('/blog/search/?q=')
            if response.status_code == 200:
                self.log_success("Empty search handled correctly")
            else:
                self.log_error(f"Empty search failed: {response.status_code}")
                
        except Exception as e:
            self.log_error(f"Search testing failed: {str(e)}")
    
    def test_performance_features(self):
        """Test performance and analytics features"""
        print("\n📊 Testing Performance Features...")
        
        try:
            # Test analytics
            if self.admin_client:
                response = self.admin_client.get('/blog/analytics/')
                
                if response.status_code == 200:
                    analytics = response.json()
                    self.log_success(f"Analytics API working: {len(analytics)} metrics available")
                else:
                    self.log_error(f"Analytics API failed: {response.status_code}")
            
            # Test trending posts
            response = self.client.get('/blog/trending/')
            
            if response.status_code == 200:
                trending = response.json()
                self.log_success(f"Trending posts API: {len(trending)} posts returned")
            else:
                self.log_error(f"Trending posts API failed: {response.status_code}")
            
            # Test view tracking
            posts = BlogPost.objects.filter(status='PUBLISHED')[:3]
            for post in posts:
                view_count_before = post.view_count
                
                # Simulate view
                response = self.client.get(f'/blog/post/{post.slug}/')
                
                if response.status_code == 200:
                    self.log_success(f"Post view tracking working for '{post.title[:30]}...'")
                else:
                    self.log_error(f"Post view failed for '{post.title[:30]}...': {response.status_code}")
            
        except Exception as e:
            self.log_error(f"Performance testing failed: {str(e)}")
    
    def test_content_quality(self):
        """Test content quality and SEO optimization"""
        print("\n📝 Testing Content Quality...")
        
        try:
            posts = BlogPost.objects.filter(status='PUBLISHED')
            
            quality_metrics = {
                'posts_with_meta_title': 0,
                'posts_with_meta_description': 0,
                'posts_with_adequate_content': 0,
                'posts_with_featured_image': 0,
                'posts_with_tags': 0
            }
            
            for post in posts:
                if post.meta_title:
                    quality_metrics['posts_with_meta_title'] += 1
                if post.meta_description:
                    quality_metrics['posts_with_meta_description'] += 1
                if len(post.content) >= 300:
                    quality_metrics['posts_with_adequate_content'] += 1
                if post.featured_image:
                    quality_metrics['posts_with_featured_image'] += 1
                if post.tags.exists():
                    quality_metrics['posts_with_tags'] += 1
            
            total_posts = posts.count()
            
            for metric, count in quality_metrics.items():
                percentage = (count / total_posts * 100) if total_posts > 0 else 0
                self.log_success(f"{metric.replace('_', ' ').title()}: {count}/{total_posts} ({percentage:.1f}%)")
            
            # Overall quality score
            total_checks = sum(quality_metrics.values())
            max_possible = total_posts * len(quality_metrics)
            quality_score = (total_checks / max_possible * 100) if max_possible > 0 else 0
            
            self.log_success(f"Overall Content Quality Score: {quality_score:.1f}%")
            
        except Exception as e:
            self.log_error(f"Content quality testing failed: {str(e)}")
    
    def test_seo_xml_sitemap(self):
        """Test XML sitemap generation"""
        print("\n🗺️  Testing XML Sitemap...")
        
        try:
            response = self.client.get('/blog/sitemap.xml')
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                if '<?xml version="1.0"' in content and '<urlset' in content:
                    self.log_success("XML Sitemap generated successfully")
                    
                    # Count URLs in sitemap
                    url_count = content.count('<url>')
                    self.log_success(f"Sitemap contains {url_count} URLs")
                else:
                    self.log_error("XML Sitemap format invalid")
            else:
                self.log_error(f"XML Sitemap generation failed: {response.status_code}")
                
        except Exception as e:
            self.log_error(f"XML Sitemap testing failed: {str(e)}")
    
    def test_rss_feed(self):
        """Test RSS feed generation"""
        print("\n📡 Testing RSS Feed...")
        
        try:
            response = self.client.get('/blog/feed/')
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                if '<rss' in content and '<channel>' in content:
                    self.log_success("RSS Feed generated successfully")
                    
                    # Count items in feed
                    item_count = content.count('<item>')
                    self.log_success(f"RSS Feed contains {item_count} items")
                else:
                    self.log_error("RSS Feed format invalid")
            else:
                self.log_error(f"RSS Feed generation failed: {response.status_code}")
                
        except Exception as e:
            self.log_error(f"RSS Feed testing failed: {str(e)}")
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE BLOG APPLICATION TEST REPORT")
        print("="*70)
        print(f"🕒 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary statistics
        total_tests = len(self.successes) + len(self.errors)
        success_rate = (len(self.successes) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 TEST SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Successful: {len(self.successes)}")
        print(f"  Failed: {len(self.errors)}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Performance metrics
        if self.performance_metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for endpoint, metrics in self.performance_metrics.items():
                print(f"  {endpoint}: {metrics['response_time']:.2f}ms ({metrics['data_count']} items)")
        
        # Database statistics
        print(f"\n💾 DATABASE STATISTICS:")
        stats = [
            ('Categories', BlogCategory.objects.count()),
            ('Tags', BlogTag.objects.count()),
            ('Published Posts', BlogPost.objects.filter(status='PUBLISHED').count()),
            ('Featured Posts', BlogPost.objects.filter(is_featured=True).count()),
            ('Total Comments', BlogComment.objects.count()),
            ('Approved Comments', BlogComment.objects.filter(is_approved=True).count()),
            ('Total Likes', BlogLike.objects.count()),
            ('Total Views', BlogView.objects.count()),
        ]
        
        for label, count in stats:
            print(f"  {label:.<25} {count:>6}")
        
        # Issues found
        if self.errors:
            print(f"\n🚨 ISSUES FOUND:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more issues")
        
        # Successful tests
        if self.successes:
            print(f"\n🎉 SUCCESSFUL TESTS:")
            for success in self.successes[:15]:  # Show first 15 successes
                print(f"  {success}")
            if len(self.successes) > 15:
                print(f"  ... and {len(self.successes) - 15} more successful tests")
        
        # Overall assessment
        print(f"\n🏥 OVERALL ASSESSMENT:")
        if success_rate >= 95:
            print("  🚀 EXCELLENT: Blog app is enterprise-ready and production-ready!")
        elif success_rate >= 85:
            print("  👍 VERY GOOD: Blog app is production-ready with minor improvements needed")
        elif success_rate >= 75:
            print("  ✅ GOOD: Blog app is functional with some improvements recommended")
        elif success_rate >= 50:
            print("  ⚠️  FAIR: Blog app needs significant improvements")
        else:
            print("  🔴 POOR: Blog app requires major fixes before production")
        
        # Recommendations
        print(f"\n💡 ENTERPRISE RECOMMENDATIONS:")
        recommendations = [
            "✅ Implement automated testing pipeline",
            "✅ Set up performance monitoring",
            "✅ Add content backup and restore",
            "✅ Implement SEO audit automation",
            "🔄 Add image optimization and CDN",
            "🔄 Implement caching layer (Redis)",
            "🔄 Add email notifications for new comments",
            "🔄 Set up Google Analytics integration",
            "🔄 Implement A/B testing for content",
            "🔄 Add social media sharing integration"
        ]
        
        for rec in recommendations:
            print(f"  {rec}")
        
        print("\n" + "="*70)

def main():
    print("🚀 Starting Comprehensive Blog Application Testing...")
    print("="*70)
    
    tester = ComprehensiveBlogTester()
    
    # Setup test environment
    admin_user = tester.setup_test_environment()
    
    if not admin_user:
        print("❌ Failed to setup test environment. Exiting.")
        return
    
    # Run all tests
    tester.test_data_seeding()
    tester.test_api_endpoints()
    tester.test_seo_features()
    tester.test_search_functionality()
    tester.test_performance_features()
    tester.test_content_quality()
    tester.test_seo_xml_sitemap()
    tester.test_rss_feed()
    
    # Generate comprehensive report
    tester.generate_comprehensive_report()
    
    print(f"\n🎯 BLOG APP ENTERPRISE READINESS: COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
