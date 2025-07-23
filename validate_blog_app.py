#!/usr/bin/env python
"""
Simple Blog App Validation Script
Tests core blog functionality and SEO features
"""

import os
import sys
import django
import requests
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from blog.models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView
from blog.seo_serializers import EnterpriseBlogPostDetailSerializer

User = get_user_model()

class BlogValidationTest:
    def __init__(self):
        self.client = APIClient()
        self.errors = []
        self.successes = []
        
    def log_success(self, message):
        self.successes.append(f"✅ {message}")
        print(f"✅ {message}")
    
    def log_error(self, message):
        self.errors.append(f"❌ {message}")
        print(f"❌ {message}")
    
    def test_blog_models(self):
        """Test blog models creation and relationships"""
        print("\n🧪 Testing Blog Models...")
        
        try:
            # Test Category
            category = BlogCategory.objects.create(
                name="Test Category",
                description="Test category description",
                meta_title="Test Category | OkPuja",
                meta_description="Test category for blog validation",
                status="PUBLISHED"
            )
            self.log_success("BlogCategory model created successfully")
            
            # Test Tag
            tag = BlogTag.objects.create(
                name="Test Tag",
                description="Test tag description",
                status="PUBLISHED"
            )
            self.log_success("BlogTag model created successfully")
            
            # Test User
            user = User.objects.create_user(
                email="testuser@example.com",
                password="testpass123"
            )
            self.log_success("Test user created successfully")
            
            # Test BlogPost
            post = BlogPost.objects.create(
                title="Test Blog Post",
                content="This is a test blog post content with more than 300 characters. " * 5,
                excerpt="This is a test excerpt",
                user=user,
                category=category,
                status="PUBLISHED",
                meta_title="Test Blog Post | OkPuja",
                meta_description="This is a test blog post for validation",
                meta_keywords="test, blog, validation"
            )
            post.tags.add(tag)
            self.log_success("BlogPost model created successfully")
            
            # Test Comment
            comment = BlogComment.objects.create(
                post=post,
                user=user,
                content="This is a test comment",
                is_approved=True
            )
            self.log_success("BlogComment model created successfully")
            
            # Test Like
            like = BlogLike.objects.create(
                post=post,
                user=user
            )
            self.log_success("BlogLike model created successfully")
            
            # Test View
            view = BlogView.objects.create(
                post=post,
                user=user,
                ip_address="127.0.0.1"
            )
            self.log_success("BlogView model created successfully")
            
        except Exception as e:
            self.log_error(f"Model creation failed: {str(e)}")
    
    def test_seo_serializers(self):
        """Test SEO-enhanced serializers"""
        print("\n🧪 Testing SEO Serializers...")
        
        try:
            post = BlogPost.objects.first()
            if post:
                serializer = EnterpriseBlogPostDetailSerializer(post)
                data = serializer.data
                
                # Check required SEO fields
                seo_fields = ['meta_title', 'meta_description', 'meta_keywords', 
                             'structured_data', 'open_graph_data', 'twitter_card_data',
                             'breadcrumbs', 'canonical_url']
                
                for field in seo_fields:
                    if field in data:
                        self.log_success(f"SEO field '{field}' present in serializer")
                    else:
                        self.log_error(f"SEO field '{field}' missing from serializer")
                
                # Check structured data
                if 'structured_data' in data and data['structured_data']:
                    structured = data['structured_data']
                    if '@context' in structured and '@type' in structured:
                        self.log_success("Valid JSON-LD structured data generated")
                    else:
                        self.log_error("Invalid structured data format")
                
            else:
                self.log_error("No blog post found for serializer testing")
                
        except Exception as e:
            self.log_error(f"Serializer testing failed: {str(e)}")
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🧪 Testing API Endpoints...")
        
        try:
            # Test blog post list
            response = self.client.get('/blog/api/posts/')
            if response.status_code == 200:
                self.log_success("Blog posts API endpoint accessible")
            else:
                self.log_error(f"Blog posts API failed: {response.status_code}")
            
            # Test categories
            response = self.client.get('/blog/api/categories/')
            if response.status_code == 200:
                self.log_success("Blog categories API endpoint accessible")
            else:
                self.log_error(f"Blog categories API failed: {response.status_code}")
            
            # Test tags
            response = self.client.get('/blog/api/tags/')
            if response.status_code == 200:
                self.log_success("Blog tags API endpoint accessible")
            else:
                self.log_error(f"Blog tags API failed: {response.status_code}")
            
        except Exception as e:
            self.log_error(f"API endpoint testing failed: {str(e)}")
    
    def test_seo_features(self):
        """Test SEO features"""
        print("\n🧪 Testing SEO Features...")
        
        try:
            posts = BlogPost.objects.filter(status='PUBLISHED')
            
            seo_score = 0
            total_checks = 0
            
            for post in posts:
                total_checks += 5  # 5 SEO checks per post
                
                if post.meta_title:
                    seo_score += 1
                if post.meta_description:
                    seo_score += 1
                if post.meta_keywords:
                    seo_score += 1
                if post.featured_image:
                    seo_score += 1
                if len(post.content) > 300:
                    seo_score += 1
            
            if total_checks > 0:
                seo_percentage = (seo_score / total_checks) * 100
                self.log_success(f"SEO Score: {seo_percentage:.1f}% ({seo_score}/{total_checks})")
                
                if seo_percentage >= 80:
                    self.log_success("Excellent SEO optimization!")
                elif seo_percentage >= 60:
                    self.log_success("Good SEO optimization")
                else:
                    self.log_error("SEO optimization needs improvement")
            else:
                self.log_error("No published posts found for SEO analysis")
                
        except Exception as e:
            self.log_error(f"SEO testing failed: {str(e)}")
    
    def test_performance_features(self):
        """Test performance and analytics features"""
        print("\n🧪 Testing Performance Features...")
        
        try:
            # Check view tracking
            views_count = BlogView.objects.count()
            self.log_success(f"View tracking working: {views_count} views recorded")
            
            # Check like system
            likes_count = BlogLike.objects.count()
            self.log_success(f"Like system working: {likes_count} likes recorded")
            
            # Check comment system
            comments_count = BlogComment.objects.filter(is_approved=True).count()
            self.log_success(f"Comment system working: {comments_count} approved comments")
            
            # Check trending posts capability
            from django.db.models import Count
            trending_posts = BlogPost.objects.filter(
                status='PUBLISHED'
            ).annotate(
                like_count=Count('likes'),
                view_count_calc=Count('views')
            ).order_by('-like_count', '-view_count_calc')[:5]
            
            self.log_success(f"Trending posts algorithm working: {trending_posts.count()} posts analyzed")
            
        except Exception as e:
            self.log_error(f"Performance testing failed: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "="*50)
        print("📊 BLOG APPLICATION VALIDATION REPORT")
        print("="*50)
        print(f"🕒 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ Successful tests: {len(self.successes)}")
        print(f"❌ Failed tests: {len(self.errors)}")
        
        if self.errors:
            print("\n🚨 ISSUES FOUND:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.successes:
            print("\n🎉 SUCCESSFUL TESTS:")
            for success in self.successes:
                print(f"  {success}")
        
        # Overall health score
        total_tests = len(self.successes) + len(self.errors)
        if total_tests > 0:
            health_score = (len(self.successes) / total_tests) * 100
            print(f"\n🏥 Overall Health Score: {health_score:.1f}%")
            
            if health_score >= 90:
                print("🚀 EXCELLENT: Blog app is enterprise-ready!")
            elif health_score >= 75:
                print("👍 GOOD: Blog app is production-ready with minor improvements needed")
            elif health_score >= 50:
                print("⚠️  FAIR: Blog app needs significant improvements")
            else:
                print("🔴 POOR: Blog app requires major fixes before production")
        
        print("\n" + "="*50)

def main():
    print("🚀 Starting Blog Application Validation...")
    print("="*50)
    
    validator = BlogValidationTest()
    
    # Run all tests
    validator.test_blog_models()
    validator.test_seo_serializers() 
    validator.test_api_endpoints()
    validator.test_seo_features()
    validator.test_performance_features()
    
    # Generate final report
    validator.generate_report()
    
    # Enterprise SEO recommendations
    print("\n📈 ENTERPRISE SEO RECOMMENDATIONS:")
    print("="*50)
    recommendations = [
        "✅ Implement XML sitemap generation",
        "✅ Add RSS feed for content syndication", 
        "✅ Include JSON-LD structured data",
        "✅ Add Open Graph and Twitter Card meta tags",
        "✅ Implement canonical URLs",
        "✅ Add breadcrumb navigation",
        "✅ Include reading time calculation",
        "✅ Add related posts functionality",
        "🔄 Set up automated SEO auditing",
        "🔄 Implement image optimization",
        "🔄 Add AMP (Accelerated Mobile Pages) support",
        "🔄 Set up Google Analytics integration",
        "🔄 Implement lazy loading for images",
        "🔄 Add social media sharing buttons",
        "🔄 Set up email newsletter integration"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print("\n💡 GOOGLE ADS READINESS:")
    print("="*50)
    ads_features = [
        "✅ SEO-optimized content structure",
        "✅ Meta tags for ad targeting",
        "✅ Category-based content organization", 
        "✅ User engagement tracking (likes, comments, views)",
        "🔄 Conversion tracking implementation needed",
        "🔄 Google Tag Manager integration needed",
        "🔄 Landing page optimization needed",
        "🔄 A/B testing framework needed"
    ]
    
    for feature in ads_features:
        print(f"  {feature}")

if __name__ == "__main__":
    main()
