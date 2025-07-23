"""
Enterprise-Level Blog Management Commands
Provides automated tasks for blog SEO optimization and maintenance
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging

from blog.models import BlogPost, BlogView, BlogCategory, BlogTag

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate comprehensive blog SEO report and optimization suggestions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='console',
            choices=['console', 'file'],
            help='Output format (console or file)'
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='Apply automatic SEO optimizations'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        output_format = options['output']
        auto_optimize = options['optimize']
        
        self.stdout.write(
            self.style.SUCCESS(f'Generating blog SEO report for last {days} days...')
        )
        
        # Generate report
        report = self.generate_seo_report(days)
        
        # Output report
        if output_format == 'console':
            self.print_console_report(report)
        else:
            self.save_file_report(report)
        
        # Apply optimizations if requested
        if auto_optimize:
            self.apply_optimizations(report)
    
    def generate_seo_report(self, days):
        """Generate comprehensive SEO analysis report"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Overall statistics
        total_posts = BlogPost.objects.filter(status='PUBLISHED').count()
        recent_posts = BlogPost.objects.filter(
            status='PUBLISHED',
            published_at__gte=start_date
        ).count()
        
        total_views = BlogView.objects.filter(created_at__gte=start_date).count()
        
        # SEO issues analysis
        posts_without_meta_title = BlogPost.objects.filter(
            status='PUBLISHED',
            meta_title__isnull=True
        ).count()
        
        posts_without_meta_description = BlogPost.objects.filter(
            status='PUBLISHED',
            meta_description__isnull=True
        ).count()
        
        posts_without_featured_image = BlogPost.objects.filter(
            status='PUBLISHED',
            featured_image__isnull=True
        ).count()
        
        posts_short_content = BlogPost.objects.filter(
            status='PUBLISHED'
        ).extra(
            where=["LENGTH(content) < 300"]
        ).count()
        
        # Performance analysis
        top_posts = BlogPost.objects.filter(
            status='PUBLISHED'
        ).annotate(
            recent_views=Count('views', filter=Q(views__created_at__gte=start_date))
        ).order_by('-recent_views')[:10]
        
        low_performing_posts = BlogPost.objects.filter(
            status='PUBLISHED',
            published_at__lte=start_date
        ).annotate(
            recent_views=Count('views', filter=Q(views__created_at__gte=start_date))
        ).filter(recent_views__lt=5).order_by('recent_views')[:10]
        
        # Category analysis
        category_performance = BlogCategory.objects.filter(
            status='PUBLISHED'
        ).annotate(
            post_count=Count('posts', filter=Q(posts__status='PUBLISHED')),
            total_views=Count('posts__views', filter=Q(posts__views__created_at__gte=start_date))
        ).order_by('-total_views')
        
        # Tag analysis
        popular_tags = BlogTag.objects.filter(
            status='PUBLISHED'
        ).annotate(
            post_count=Count('posts', filter=Q(posts__status='PUBLISHED'))
        ).filter(post_count__gt=0).order_by('-post_count')[:20]
        
        unused_tags = BlogTag.objects.filter(
            status='PUBLISHED'
        ).annotate(
            post_count=Count('posts', filter=Q(posts__status='PUBLISHED'))
        ).filter(post_count=0)
        
        return {
            'overview': {
                'total_posts': total_posts,
                'recent_posts': recent_posts,
                'total_views': total_views,
                'analysis_period': f'{days} days'
            },
            'seo_issues': {
                'posts_without_meta_title': posts_without_meta_title,
                'posts_without_meta_description': posts_without_meta_description,
                'posts_without_featured_image': posts_without_featured_image,
                'posts_short_content': posts_short_content
            },
            'performance': {
                'top_posts': top_posts,
                'low_performing_posts': low_performing_posts
            },
            'categories': category_performance,
            'tags': {
                'popular': popular_tags,
                'unused': unused_tags
            }
        }
    
    def print_console_report(self, report):
        """Print report to console with formatting"""
        self.stdout.write(self.style.HTTP_INFO('\n=== BLOG SEO ANALYSIS REPORT ===\n'))
        
        # Overview
        overview = report['overview']
        self.stdout.write(self.style.SUCCESS('📊 OVERVIEW:'))
        self.stdout.write(f"  Total Published Posts: {overview['total_posts']}")
        self.stdout.write(f"  Recent Posts ({overview['analysis_period']}): {overview['recent_posts']}")
        self.stdout.write(f"  Total Views ({overview['analysis_period']}): {overview['total_views']}")
        
        # SEO Issues
        seo = report['seo_issues']
        self.stdout.write(self.style.WARNING('\n🔍 SEO ISSUES:'))
        if seo['posts_without_meta_title'] > 0:
            self.stdout.write(f"  ⚠️  {seo['posts_without_meta_title']} posts missing meta titles")
        if seo['posts_without_meta_description'] > 0:
            self.stdout.write(f"  ⚠️  {seo['posts_without_meta_description']} posts missing meta descriptions")
        if seo['posts_without_featured_image'] > 0:
            self.stdout.write(f"  ⚠️  {seo['posts_without_featured_image']} posts missing featured images")
        if seo['posts_short_content'] > 0:
            self.stdout.write(f"  ⚠️  {seo['posts_short_content']} posts with content < 300 characters")
        
        if all(count == 0 for count in seo.values()):
            self.stdout.write(self.style.SUCCESS("  ✅ No major SEO issues found!"))
        
        # Top Performing Posts
        self.stdout.write(self.style.SUCCESS('\n🚀 TOP PERFORMING POSTS:'))
        for i, post in enumerate(report['performance']['top_posts'][:5], 1):
            views = getattr(post, 'recent_views', 0)
            self.stdout.write(f"  {i}. {post.title} ({views} views)")
        
        # Low Performing Posts
        if report['performance']['low_performing_posts']:
            self.stdout.write(self.style.ERROR('\n📉 LOW PERFORMING POSTS:'))
            for post in report['performance']['low_performing_posts'][:5]:
                views = getattr(post, 'recent_views', 0)
                self.stdout.write(f"  • {post.title} ({views} views)")
        
        # Category Performance
        self.stdout.write(self.style.HTTP_INFO('\n📂 CATEGORY PERFORMANCE:'))
        for category in report['categories'][:5]:
            self.stdout.write(f"  • {category.name}: {category.post_count} posts, {getattr(category, 'total_views', 0)} views")
        
        # Popular Tags
        self.stdout.write(self.style.HTTP_INFO('\n🏷️  POPULAR TAGS:'))
        for tag in report['tags']['popular'][:10]:
            self.stdout.write(f"  • {tag.name} ({tag.post_count} posts)")
        
        # Unused Tags
        if report['tags']['unused']:
            self.stdout.write(self.style.WARNING(f'\n🗑️  UNUSED TAGS: {report["tags"]["unused"].count()} tags'))
    
    def apply_optimizations(self, report):
        """Apply automatic SEO optimizations"""
        self.stdout.write(self.style.WARNING('\n🔧 APPLYING AUTOMATIC OPTIMIZATIONS...\n'))
        
        optimizations_applied = 0
        
        # Auto-generate meta titles for posts without them
        posts_without_meta_title = BlogPost.objects.filter(
            status='PUBLISHED',
            meta_title__isnull=True
        )
        
        for post in posts_without_meta_title:
            # Generate meta title from post title and category
            category_name = post.category.name if post.category else 'Spirituality'
            meta_title = f"{post.title} | {category_name} | OkPuja"
            
            if len(meta_title) > 60:
                meta_title = f"{post.title[:50]}... | OkPuja"
            
            post.meta_title = meta_title
            post.save(update_fields=['meta_title'])
            optimizations_applied += 1
        
        if posts_without_meta_title.count() > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Generated meta titles for {posts_without_meta_title.count()} posts")
            )
        
        # Auto-generate meta descriptions for posts without them
        posts_without_meta_description = BlogPost.objects.filter(
            status='PUBLISHED',
            meta_description__isnull=True
        )
        
        for post in posts_without_meta_description:
            # Generate meta description from excerpt or content
            if post.excerpt:
                meta_description = post.excerpt[:155] + '...' if len(post.excerpt) > 155 else post.excerpt
            else:
                # Extract first 155 characters from content (strip HTML)
                import re
                content_text = re.sub(r'<[^>]+>', '', post.content)
                meta_description = content_text[:155] + '...' if len(content_text) > 155 else content_text
            
            post.meta_description = meta_description
            post.save(update_fields=['meta_description'])
            optimizations_applied += 1
        
        if posts_without_meta_description.count() > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Generated meta descriptions for {posts_without_meta_description.count()} posts")
            )
        
        # Clean up unused tags
        unused_tags = BlogTag.objects.filter(
            status='PUBLISHED'
        ).annotate(
            post_count=Count('posts', filter=Q(posts__status='PUBLISHED'))
        ).filter(post_count=0)
        
        if unused_tags.exists():
            unused_count = unused_tags.count()
            unused_tags.delete()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Removed {unused_count} unused tags")
            )
            optimizations_applied += unused_count
        
        if optimizations_applied > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Applied {optimizations_applied} optimizations successfully!')
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO('\n✨ No optimizations needed - blog is already well optimized!')
            )
    
    def save_file_report(self, report):
        """Save detailed report to file"""
        import json
        from datetime import datetime
        
        filename = f'blog_seo_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # Convert QuerySets to lists for JSON serialization
        serializable_report = {
            'generated_at': timezone.now().isoformat(),
            'overview': report['overview'],
            'seo_issues': report['seo_issues'],
            'performance': {
                'top_posts': [
                    {
                        'id': post.id,
                        'title': post.title,
                        'slug': post.slug,
                        'views': getattr(post, 'recent_views', 0)
                    }
                    for post in report['performance']['top_posts']
                ],
                'low_performing_posts': [
                    {
                        'id': post.id,
                        'title': post.title,
                        'slug': post.slug,
                        'views': getattr(post, 'recent_views', 0)
                    }
                    for post in report['performance']['low_performing_posts']
                ]
            },
            'categories': [
                {
                    'name': cat.name,
                    'slug': cat.slug,
                    'post_count': cat.post_count,
                    'total_views': getattr(cat, 'total_views', 0)
                }
                for cat in report['categories']
            ],
            'tags': {
                'popular': [
                    {
                        'name': tag.name,
                        'slug': tag.slug,
                        'post_count': tag.post_count
                    }
                    for tag in report['tags']['popular']
                ],
                'unused_count': report['tags']['unused'].count()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(serializable_report, f, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'📄 Detailed report saved to: {filename}')
        )
