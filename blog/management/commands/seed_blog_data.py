"""
Blog Data Seeder - Creates comprehensive test data for the blog application
Generates realistic content for categories, tags, posts, comments, likes, and views
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction
from datetime import timedelta
import random
import uuid
from faker import Faker

from blog.models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed the blog with realistic test data for development and testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            type=int,
            default=8,
            help='Number of categories to create (default: 8)'
        )
        parser.add_argument(
            '--tags',
            type=int,
            default=25,
            help='Number of tags to create (default: 25)'
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=50,
            help='Number of blog posts to create (default: 50)'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of test users to create (default: 10)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing blog data before seeding'
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.clear_existing_data()
        
        with transaction.atomic():
            users = self.create_users(options['users'])
            categories = self.create_categories(options['categories'])
            tags = self.create_tags(options['tags'])
            posts = self.create_posts(options['posts'], users, categories, tags)
            self.create_comments(posts, users)
            self.create_likes_and_views(posts, users)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded blog with realistic data!')
        )
        self.print_summary()
    
    def clear_existing_data(self):
        """Clear existing blog data"""
        self.stdout.write('Clearing existing blog data...')
        
        BlogView.objects.all().delete()
        BlogLike.objects.all().delete()
        BlogComment.objects.all().delete()
        BlogPost.objects.all().delete()
        BlogTag.objects.all().delete()
        BlogCategory.objects.all().delete()
        
        # Clear test users (keep admin users)
        User.objects.filter(email__contains='testuser').delete()
        
        self.stdout.write(self.style.SUCCESS('Existing data cleared.'))
    
    def generate_unique_slug(self, title, model_class):
        """Generate a unique slug for the given title and model class"""
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        
        # Keep trying until we find a unique slug
        while model_class.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def create_users(self, count):
        """Create test users"""
        self.stdout.write(f'Creating {count} test users...')
        
        users = []
        for i in range(count):
            # Create user
            user = User.objects.create_user(
                email=f'testuser{i+1}@okpuja.com',
                password='testpass123',
                phone=f'+91987654{i:04d}'  # Valid Indian phone format
            )
            
            # Create user profile with name
            from accounts.models import UserProfile
            UserProfile.objects.create(
                user=user,
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            
            users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users.'))
        return users
    
    def create_categories(self, count):
        """Create blog categories with Hindu spiritual themes"""
        self.stdout.write(f'Creating {count} blog categories...')
        
        category_data = [
            {
                'name': 'Puja Rituals',
                'description': 'Traditional Hindu puja ceremonies and their significance',
                'meta_keywords': 'puja, rituals, hindu ceremonies, worship, traditions'
            },
            {
                'name': 'Festival Celebrations',
                'description': 'Hindu festivals, their history and celebration methods',
                'meta_keywords': 'festivals, celebrations, diwali, holi, navratri, durga puja'
            },
            {
                'name': 'Spiritual Guidance',
                'description': 'Spiritual wisdom and guidance for daily life',
                'meta_keywords': 'spirituality, guidance, meditation, dharma, moksha'
            },
            {
                'name': 'Temple Traditions',
                'description': 'Temple architecture, traditions and significance',
                'meta_keywords': 'temples, architecture, traditions, pilgrimage, sacred places'
            },
            {
                'name': 'Vedic Astrology',
                'description': 'Ancient Vedic astrology and its modern applications',
                'meta_keywords': 'astrology, vedic, horoscope, planets, predictions'
            },
            {
                'name': 'Sacred Texts',
                'description': 'Understanding Hindu scriptures and their teachings',
                'meta_keywords': 'vedas, puranas, upanishads, bhagavad gita, ramayana'
            },
            {
                'name': 'Yoga & Meditation',
                'description': 'Ancient practices for physical and spiritual wellness',
                'meta_keywords': 'yoga, meditation, pranayama, wellness, mindfulness'
            },
            {
                'name': 'Life Ceremonies',
                'description': 'Important life events and their ritual significance',
                'meta_keywords': 'ceremonies, samskaras, wedding, birth, death rituals'
            }
        ]
        
        categories = []
        
        # Get admin user for categories (or first user if no admin exists)
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        for i, data in enumerate(category_data[:count]):
            category = BlogCategory.objects.create(
                user=admin_user,  # Add required user field
                name=data['name'],
                description=data['description'],
                meta_title=f"{data['name']} | Hindu Spiritual Guidance | OkPuja",
                meta_description=f"Explore {data['description'].lower()} with OkPuja's comprehensive spiritual guidance.",
                meta_keywords=data['meta_keywords'],
                status='PUBLISHED'
            )
            categories.append(category)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories.'))
        return categories
    
    def create_tags(self, count):
        """Create blog tags"""
        self.stdout.write(f'Creating {count} blog tags...')
        
        tag_names = [
            'Ganesh Puja', 'Durga Puja', 'Lakshmi Puja', 'Saraswati Puja', 'Shiva Puja',
            'Diwali', 'Holi', 'Navratri', 'Karva Chauth', 'Janmashtami',
            'Meditation', 'Pranayama', 'Yoga', 'Mindfulness', 'Chakras',
            'Vedas', 'Upanishads', 'Bhagavad Gita', 'Ramayana', 'Mahabharata',
            'Temples', 'Pilgrimage', 'Sacred Places', 'Mantras', 'Prayers',
            'Astrology', 'Horoscope', 'Vastu', 'Numerology', 'Gemstones',
            'Marriage', 'Birth Ceremonies', 'Death Rituals', 'Fasting', 'Vratas',
            'Spiritual Growth', 'Dharma', 'Karma', 'Moksha', 'Bhakti',
            'Hindu Philosophy', 'Ayurveda', 'Traditional Medicine', 'Herbs', 'Healing'
        ]
        
        tags = []
        for i, name in enumerate(tag_names[:count]):
            tag = BlogTag.objects.create(
                name=name,
                description=f'Posts related to {name.lower()} in Hindu spirituality',
                status='PUBLISHED'
            )
            tags.append(tag)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(tags)} tags.'))
        return tags
    
    def create_posts(self, count, users, categories, tags):
        """Create blog posts with realistic content"""
        self.stdout.write(f'Creating {count} blog posts...')
        
        post_templates = [
            {
                'title_template': 'Complete Guide to {topic} Puja: Rituals and Significance',
                'content_topics': ['Ganesh', 'Durga', 'Lakshmi', 'Saraswati', 'Shiva', 'Krishna', 'Rama'],
                'category_filter': 'Puja Rituals'
            },
            {
                'title_template': 'Celebrating {topic}: Traditions, Rituals and Modern Practices',
                'content_topics': ['Diwali', 'Holi', 'Navratri', 'Karva Chauth', 'Janmashtami', 'Ram Navami'],
                'category_filter': 'Festival Celebrations'
            },
            {
                'title_template': 'The Spiritual Significance of {topic} in Hindu Philosophy',
                'content_topics': ['Meditation', 'Yoga', 'Dharma', 'Karma', 'Moksha', 'Bhakti', 'Service'],
                'category_filter': 'Spiritual Guidance'
            },
            {
                'title_template': 'Understanding {topic}: Ancient Wisdom for Modern Life',
                'content_topics': ['Vedic Astrology', 'Ayurveda', 'Vastu Shastra', 'Gemstone Therapy'],
                'category_filter': 'Vedic Astrology'
            }
        ]
        
        posts = []
        for i in range(count):
            template = random.choice(post_templates)
            topic = random.choice(template['content_topics'])
            
            # Find matching category
            category = next(
                (cat for cat in categories if template['category_filter'] in cat.name),
                random.choice(categories)
            )
            
            title = template['title_template'].format(topic=topic)
            
            # Generate unique slug for this post
            unique_slug = self.generate_unique_slug(title, BlogPost)
            
            # Generate content
            content = self.generate_blog_content(topic, title)
            excerpt = fake.text(max_nb_chars=200)
            
            # Create the post with explicit unique slug
            post = BlogPost.objects.create(
                title=title,
                slug=unique_slug,  # Set unique slug explicitly
                content=content,
                excerpt=excerpt,
                user=random.choice(users),
                category=category,
                status='PUBLISHED',
                meta_title=f"{title} | OkPuja Spiritual Guide",
                meta_description=f"Discover the spiritual significance of {topic.lower()}. {excerpt[:100]}...",
                meta_keywords=f"{topic.lower()}, hindu spirituality, puja, rituals, traditions",
                is_featured=random.choice([True, False]) if random.random() < 0.3 else False,
                published_at=timezone.now() - timedelta(days=random.randint(0, 365))
            )
            
            # Add random tags
            post_tags = random.sample(tags, random.randint(2, 5))
            post.tags.set(post_tags)
            
            posts.append(post)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(posts)} blog posts.'))
        return posts
    
    def generate_blog_content(self, topic, title):
        """Generate realistic blog content"""
        content_parts = [
            f"# {title}\n\n",
            f"## Introduction\n\n{fake.text(max_nb_chars=300)}\n\n",
            f"## Historical Significance of {topic}\n\n{fake.text(max_nb_chars=400)}\n\n",
            f"## Traditional Practices\n\n{fake.text(max_nb_chars=350)}\n\n",
            f"### Step-by-Step Ritual Guide\n\n",
            f"1. **Preparation**: {fake.text(max_nb_chars=150)}\n",
            f"2. **Invocation**: {fake.text(max_nb_chars=150)}\n",
            f"3. **Main Ritual**: {fake.text(max_nb_chars=150)}\n",
            f"4. **Conclusion**: {fake.text(max_nb_chars=150)}\n\n",
            f"## Modern Relevance\n\n{fake.text(max_nb_chars=300)}\n\n",
            f"## Benefits and Spiritual Impact\n\n{fake.text(max_nb_chars=250)}\n\n",
            f"## Conclusion\n\n{fake.text(max_nb_chars=200)}\n\n",
            f"*For personalized guidance on {topic.lower()} rituals, consult with our experienced spiritual advisors at OkPuja.*"
        ]
        
        return ''.join(content_parts)
    
    def create_comments(self, posts, users):
        """Create realistic comments on blog posts"""
        self.stdout.write('Creating blog comments...')
        
        comment_templates = [
            "Thank you for this detailed explanation! Very helpful for understanding the significance.",
            "I've been looking for authentic information about this ritual. Great article!",
            "This is exactly what I needed to know. The step-by-step guide is very clear.",
            "Beautiful explanation of the spiritual aspects. Much appreciated!",
            "I learned so much from this post. Thank you for sharing your knowledge.",
            "Excellent content! This will help me perform the ritual correctly.",
            "Very informative article. I'll definitely follow these guidelines.",
            "The historical context provided here is fascinating. Thank you!",
            "This answered all my questions about the ritual. Wonderfully written!",
            "Such authentic information is hard to find. Great work!"
        ]
        
        comments_created = 0
        for post in posts:
            # Random number of comments per post (0-8)
            num_comments = random.randint(0, 8)
            
            for _ in range(num_comments):
                comment = BlogComment.objects.create(
                    post=post,
                    user=random.choice(users),
                    content=random.choice(comment_templates),
                    is_approved=random.choice([True, True, True, False]),  # 75% approved
                    created_at=post.published_at + timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23)
                    )
                )
                comments_created += 1
                
                # Occasionally create replies
                if random.random() < 0.3:  # 30% chance of reply
                    BlogComment.objects.create(
                        post=post,
                        user=random.choice(users),
                        parent=comment,
                        content="Thank you for your comment! I'm glad you found it helpful.",
                        is_approved=True,
                        created_at=comment.created_at + timedelta(hours=random.randint(1, 48))
                    )
                    comments_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {comments_created} comments.'))
    
    def create_likes_and_views(self, posts, users):
        """Create likes and views for blog posts"""
        self.stdout.write('Creating likes and views...')
        
        likes_created = 0
        views_created = 0
        
        for post in posts:
            # Create views (more views than likes)
            num_views = random.randint(50, 500)
            view_users = random.sample(users, min(len(users), random.randint(1, len(users))))
            
            for i in range(num_views):
                # Some views from registered users, some anonymous
                user = random.choice(view_users) if random.random() < 0.7 else None
                ip_address = f"192.168.1.{random.randint(1, 254)}"
                
                view_time = post.published_at + timedelta(
                    days=random.randint(0, 60),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                BlogView.objects.create(
                    post=post,
                    user=user,
                    ip_address=ip_address,
                    created_at=view_time
                )
                views_created += 1
            
            # Update post view count
            post.view_count = num_views
            post.save(update_fields=['view_count'])
            
            # Create likes (subset of viewers)
            num_likes = random.randint(0, min(num_views // 10, len(users)))
            like_users = random.sample(users, num_likes)
            
            for user in like_users:
                BlogLike.objects.create(
                    post=post,
                    user=user,
                    created_at=post.published_at + timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23)
                    )
                )
                likes_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {views_created} views and {likes_created} likes.'))
    
    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.HTTP_INFO('BLOG DATA SEEDING SUMMARY'))
        self.stdout.write('='*50)
        
        summary_data = [
            ('Users', User.objects.filter(email__contains='testuser').count()),
            ('Categories', BlogCategory.objects.count()),
            ('Tags', BlogTag.objects.count()),
            ('Published Posts', BlogPost.objects.filter(status='PUBLISHED').count()),
            ('Draft Posts', BlogPost.objects.filter(status='DRAFT').count()),
            ('Featured Posts', BlogPost.objects.filter(is_featured=True).count()),
            ('Total Comments', BlogComment.objects.count()),
            ('Approved Comments', BlogComment.objects.filter(is_approved=True).count()),
            ('Total Likes', BlogLike.objects.count()),
            ('Total Views', BlogView.objects.count()),
        ]
        
        for label, count in summary_data:
            self.stdout.write(f'{label:.<20} {count:>5}')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎉 Blog seeding completed successfully!'))
        self.stdout.write(self.style.HTTP_INFO('Your blog is now ready for testing with realistic data.'))
        self.stdout.write('='*50)
