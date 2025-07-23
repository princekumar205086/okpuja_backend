"""
Automated SEO Optimization and Content Enhancement Command
Automatically improves blog content for better search engine optimization
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.template.defaultfilters import truncatewords
from datetime import timedelta
import re
import requests
from textstat import flesch_reading_ease, flesch_kincaid_grade
from collections import Counter

from blog.models import BlogPost, BlogCategory, BlogTag

class Command(BaseCommand):
    help = 'Automatically optimize blog content for SEO and user engagement'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--posts',
            type=int,
            default=10,
            help='Number of recent posts to optimize (default: 10)'
        )
        parser.add_argument(
            '--mode',
            type=str,
            default='all',
            choices=['meta', 'content', 'keywords', 'all'],
            help='Optimization mode (default: all)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force optimization even if content already exists'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be optimized without making changes'
        )
    
    def handle(self, *args, **options):
        posts_count = options['posts']
        mode = options['mode']
        force = options['force']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE: No changes will be made')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting SEO optimization for {posts_count} posts...')
        )
        
        # Get posts to optimize
        posts = BlogPost.objects.filter(status='PUBLISHED').order_by('-updated_at')[:posts_count]
        
        optimization_stats = {
            'meta_titles': 0,
            'meta_descriptions': 0,
            'meta_keywords': 0,
            'content_improvements': 0,
            'readability_improvements': 0
        }
        
        for post in posts:
            self.stdout.write(f'\nOptimizing: {post.title}')
            
            if mode in ['meta', 'all']:
                # Optimize meta tags
                if self.optimize_meta_title(post, force, dry_run):
                    optimization_stats['meta_titles'] += 1
                
                if self.optimize_meta_description(post, force, dry_run):
                    optimization_stats['meta_descriptions'] += 1
                
                if self.optimize_meta_keywords(post, force, dry_run):
                    optimization_stats['meta_keywords'] += 1
            
            if mode in ['content', 'all']:
                # Optimize content structure
                if self.optimize_content_structure(post, force, dry_run):
                    optimization_stats['content_improvements'] += 1
                
                # Improve readability
                if self.improve_readability(post, force, dry_run):
                    optimization_stats['readability_improvements'] += 1
            
            if mode in ['keywords', 'all']:
                # Optimize keyword density
                self.analyze_keyword_density(post)
            
            if not dry_run:
                post.save()
        
        # Print summary
        self.print_optimization_summary(optimization_stats, dry_run)
    
    def optimize_meta_title(self, post, force, dry_run):
        """Optimize meta title for SEO"""
        if post.meta_title and not force:
            return False
        
        # Generate optimized meta title
        category_name = post.category.name if post.category else ''
        brand_name = 'OkPuja'
        
        # Title variations based on category
        if 'puja' in post.title.lower() or 'ritual' in post.title.lower():
            template = f"{post.title} | Complete Guide | {brand_name}"
        elif 'festival' in post.title.lower():
            template = f"{post.title} | Celebration Guide | {brand_name}"
        elif category_name:
            template = f"{post.title} | {category_name} | {brand_name}"
        else:
            template = f"{post.title} | Hindu Spiritual Guide | {brand_name}"
        
        # Ensure title is within SEO limits (50-60 characters)
        if len(template) > 60:
            # Truncate main title and rebuild
            max_title_length = 60 - len(f" | {brand_name}")
            if category_name:
                max_title_length -= len(f" | {category_name}")
            
            truncated_title = post.title[:max_title_length-3] + '...'
            if category_name:
                template = f"{truncated_title} | {category_name} | {brand_name}"
            else:
                template = f"{truncated_title} | {brand_name}"
        
        if not dry_run:
            post.meta_title = template
        
        self.stdout.write(f"  ✅ Meta title: {template}")
        return True
    
    def optimize_meta_description(self, post, force, dry_run):
        """Optimize meta description for SEO"""
        if post.meta_description and not force:
            return False
        
        # Use excerpt if available, otherwise generate from content
        if post.excerpt:
            base_description = post.excerpt
        else:
            # Extract first paragraph or 150 characters
            content_text = re.sub(r'<[^>]+>', '', post.content)  # Remove HTML
            content_text = re.sub(r'#.*\n', '', content_text)    # Remove markdown headers
            base_description = content_text[:150].strip()
        
        # Add call-to-action and ensure it's within 155-160 characters
        cta_phrases = [
            "Learn more about Hindu traditions with OkPuja.",
            "Discover authentic spiritual practices at OkPuja.",
            "Get expert guidance on Hindu rituals at OkPuja.",
            "Explore the spiritual significance with OkPuja."
        ]
        
        # Choose CTA based on content
        if 'puja' in post.title.lower():
            cta = cta_phrases[2]
        elif 'festival' in post.title.lower():
            cta = cta_phrases[1]
        else:
            cta = cta_phrases[0]
        
        # Combine and ensure proper length
        full_description = f"{base_description.rstrip('.')}. {cta}"
        
        if len(full_description) > 160:
            # Truncate base description to fit
            max_base_length = 160 - len(cta) - 2  # 2 for ". "
            base_description = base_description[:max_base_length].rstrip('.')
            full_description = f"{base_description}. {cta}"
        
        if not dry_run:
            post.meta_description = full_description
        
        self.stdout.write(f"  ✅ Meta description: {full_description[:50]}...")
        return True
    
    def optimize_meta_keywords(self, post, force, dry_run):
        """Generate optimized meta keywords"""
        if post.meta_keywords and not force:
            return False
        
        keywords = []
        
        # Extract keywords from tags
        if post.tags.exists():
            keywords.extend([tag.name.lower() for tag in post.tags.all()])
        
        # Extract keywords from category
        if post.category:
            keywords.append(post.category.name.lower())
        
        # Extract keywords from title
        title_words = re.findall(r'\b\w+\b', post.title.lower())
        significant_words = [word for word in title_words if len(word) > 3]
        keywords.extend(significant_words[:3])  # Add top 3 significant words
        
        # Add general spiritual keywords
        spiritual_keywords = [
            'hindu spirituality', 'spiritual guidance', 'indian traditions',
            'religious practices', 'spiritual wisdom', 'okpuja'
        ]
        
        # Select most relevant spiritual keywords
        for keyword in spiritual_keywords:
            if any(word in post.content.lower() for word in keyword.split()):
                keywords.append(keyword)
            if len(keywords) >= 8:  # Limit to 8 keywords
                break
        
        # Remove duplicates and create final keyword string
        unique_keywords = list(dict.fromkeys(keywords))  # Preserve order
        keyword_string = ', '.join(unique_keywords[:8])
        
        if not dry_run:
            post.meta_keywords = keyword_string
        
        self.stdout.write(f"  ✅ Meta keywords: {keyword_string}")
        return True
    
    def optimize_content_structure(self, post, force, dry_run):
        """Improve content structure for better SEO"""
        content = post.content
        improvements_made = False
        
        # Check for proper heading structure
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        if not headings:
            # Add basic heading structure if none exists
            paragraphs = content.split('\n\n')
            if len(paragraphs) > 3:
                # Add headings to major sections
                structured_content = f"## Introduction\n\n{paragraphs[0]}\n\n"
                
                # Add middle sections with headings
                for i, paragraph in enumerate(paragraphs[1:-1], 1):
                    if len(paragraph) > 100:  # Only add headings to substantial paragraphs
                        structured_content += f"## Key Point {i}\n\n{paragraph}\n\n"
                    else:
                        structured_content += f"{paragraph}\n\n"
                
                # Add conclusion
                structured_content += f"## Conclusion\n\n{paragraphs[-1]}"
                
                if not dry_run:
                    post.content = structured_content
                
                self.stdout.write("  ✅ Added heading structure")
                improvements_made = True
        
        # Ensure proper paragraph length (not too long)
        paragraphs = content.split('\n\n')
        long_paragraphs = [p for p in paragraphs if len(p) > 500]
        
        if long_paragraphs:
            self.stdout.write(f"  ⚠️  Found {len(long_paragraphs)} long paragraphs (consider breaking them up)")
        
        return improvements_made
    
    def improve_readability(self, post, force, dry_run):
        """Analyze and suggest readability improvements"""
        try:
            # Calculate readability scores
            content_text = re.sub(r'<[^>]+>', '', post.content)  # Remove HTML
            content_text = re.sub(r'#.*\n', '', content_text)    # Remove headers
            
            if len(content_text) < 100:
                return False
            
            flesch_score = flesch_reading_ease(content_text)
            grade_level = flesch_kincaid_grade(content_text)
            
            # Ideal scores: Flesch 60-70 (fairly easy), Grade level 8-10
            readability_issues = []
            
            if flesch_score < 50:
                readability_issues.append("Text is too difficult to read")
            elif flesch_score > 80:
                readability_issues.append("Text might be too simple")
            
            if grade_level > 12:
                readability_issues.append("Grade level too high")
            
            if readability_issues:
                self.stdout.write(f"  📊 Readability - Flesch: {flesch_score:.1f}, Grade: {grade_level:.1f}")
                for issue in readability_issues:
                    self.stdout.write(f"    ⚠️  {issue}")
            else:
                self.stdout.write(f"  ✅ Good readability - Flesch: {flesch_score:.1f}, Grade: {grade_level:.1f}")
            
            return len(readability_issues) > 0
            
        except Exception as e:
            self.stdout.write(f"  ❌ Readability analysis failed: {str(e)}")
            return False
    
    def analyze_keyword_density(self, post):
        """Analyze keyword density and suggest improvements"""
        content_text = re.sub(r'<[^>]+>', '', post.content.lower())
        words = re.findall(r'\b\w+\b', content_text)
        
        if len(words) < 100:
            return
        
        word_count = Counter(words)
        total_words = len(words)
        
        # Analyze primary keywords from title
        title_words = re.findall(r'\b\w+\b', post.title.lower())
        primary_keywords = [word for word in title_words if len(word) > 3]
        
        self.stdout.write("  📈 Keyword Analysis:")
        
        for keyword in primary_keywords[:3]:  # Check top 3 keywords
            density = (word_count.get(keyword, 0) / total_words) * 100
            
            if density < 0.5:
                status = "❌ Too low"
            elif density > 3:
                status = "⚠️  Too high"
            else:
                status = "✅ Good"
            
            self.stdout.write(f"    '{keyword}': {density:.1f}% {status}")
    
    def print_optimization_summary(self, stats, dry_run):
        """Print optimization summary"""
        mode_text = "DRY RUN - " if dry_run else ""
        
        self.stdout.write(f'\n{mode_text}OPTIMIZATION SUMMARY:')
        self.stdout.write('=' * 50)
        
        for metric, count in stats.items():
            metric_name = metric.replace('_', ' ').title()
            self.stdout.write(f'{metric_name}: {count}')
        
        total_optimizations = sum(stats.values())
        self.stdout.write(f'\nTotal Optimizations: {total_optimizations}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nRun without --dry-run to apply optimizations')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Blog SEO optimization completed!')
            )
