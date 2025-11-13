#!/usr/bin/env python3
"""
Script to check and validate news images in index.html
Identifies news items without proper images and provides fixes
"""

import re
import os
from pathlib import Path

def check_news_images(html_file_path):
    """Check all news items for missing or broken images"""
    
    print("=" * 80)
    print("NEWS IMAGE CHECKER")
    print("=" * 80)
    
    if not os.path.exists(html_file_path):
        print(f"❌ Error: File not found: {html_file_path}")
        return
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all news items
    news_pattern = r'<article class="news-item">(.*?)</article>'
    news_items = re.findall(news_pattern, content, re.DOTALL)
    
    print(f"\n📰 Found {len(news_items)} news items\n")
    
    issues_found = []
    
    for idx, item in enumerate(news_items, 1):
        # Extract title
        title_match = re.search(r'<h3 class="news-item-title">(.*?)</h3>', item)
        title = title_match.group(1) if title_match else "No title"
        
        # Check for thumbnail div
        has_thumbnail = '<div class="news-thumbnail">' in item
        
        # Check for img tag
        img_match = re.search(r'<img src="([^"]*)"', item)
        has_img = img_match is not None
        img_src = img_match.group(1) if has_img else None
        
        # Check for category
        category_match = re.search(r'<div class="news-category[^"]*">(.*?)</div>', item)
        category = category_match.group(1) if category_match else "No category"
        
        print(f"📄 Item {idx}: {title[:60]}...")
        print(f"   Category: {category}")
        
        if not has_thumbnail:
            print(f"   ⚠️  WARNING: Missing news-thumbnail div")
            issues_found.append({
                'item': idx,
                'title': title,
                'issue': 'missing_thumbnail_div'
            })
        
        if not has_img:
            print(f"   ❌ ERROR: Missing image tag")
            issues_found.append({
                'item': idx,
                'title': title,
                'issue': 'missing_image_tag'
            })
        else:
            print(f"   ✅ Image found: {img_src[:50]}...")
            
            # Check if it's a valid URL
            if not (img_src.startswith('http://') or img_src.startswith('https://')):
                print(f"   ⚠️  WARNING: Image source is not a valid URL")
                issues_found.append({
                    'item': idx,
                    'title': title,
                    'issue': 'invalid_image_url',
                    'src': img_src
                })
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if not issues_found:
        print("✅ All news items have proper images!")
    else:
        print(f"❌ Found {len(issues_found)} issues:\n")
        for issue in issues_found:
            print(f"  - Item {issue['item']}: {issue['title'][:50]}...")
            print(f"    Issue: {issue['issue']}")
            if 'src' in issue:
                print(f"    Source: {issue['src']}")
            print()
    
    return issues_found


def suggest_images_for_categories():
    """Suggest high-quality Unsplash images for different categories"""
    
    image_library = {
        'GIÁ CÀ PHÊ': [
            'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400&h=300&fit=crop',  # Coffee beans
            'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&h=300&fit=crop',  # Coffee cherries
            'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=300&fit=crop',  # Coffee plantation
        ],
        'XUẤT KHẨU': [
            'https://images.unsplash.com/photo-1578632292335-df3abbb0d586?w=400&h=300&fit=crop',  # Coffee bags export
            'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=400&h=300&fit=crop',  # Shipping containers
            'https://images.unsplash.com/photo-1494412685616-a5d310fbb07d?w=400&h=300&fit=crop',  # Coffee production
        ],
        'DỰ BÁO': [
            'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=300&fit=crop',  # Coffee farm
            'https://images.unsplash.com/photo-1587734195503-904fca47ad4b?w=400&h=300&fit=crop',  # Coffee plantation rows
            'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=300&fit=crop',  # Coffee landscape
        ],
        'THỊ TRƯỜNG': [
            'https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=400&h=300&fit=crop',  # Coffee market
            'https://images.unsplash.com/photo-1556742031-c6961e8560b0?w=400&h=300&fit=crop',  # Coffee trading
            'https://images.unsplash.com/photo-1511920170033-f8396924c348?w=400&h=300&fit=crop',  # Coffee bags
        ],
        'CHÍNH SÁCH': [
            'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=300&fit=crop',  # Coffee policy
            'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400&h=300&fit=crop',  # Coffee beans close up
            'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=300&fit=crop',  # Coffee farm development
        ],
        'CÔNG NGHỆ': [
            'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=300&fit=crop',  # Coffee technology
            'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=300&fit=crop',  # Modern coffee
            'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400&h=300&fit=crop',  # Coffee processing
        ],
        'QUỐC TẾ': [
            'https://images.unsplash.com/photo-1511920170033-f8396924c348?w=400&h=300&fit=crop',  # International market
            'https://images.unsplash.com/photo-1578632292335-df3abbb0d586?w=400&h=300&fit=crop',  # Global coffee
            'https://images.unsplash.com/photo-1556742031-c6961e8560b0?w=400&h=300&fit=crop',  # World trade
        ],
        'BỀN VỮNG': [
            'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=300&fit=crop',  # Sustainable farming
            'https://images.unsplash.com/photo-1587734195503-904fca47ad4b?w=400&h=300&fit=crop',  # Green coffee
            'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=300&fit=crop',  # Eco coffee
        ],
        'TIN TỨC': [
            'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=300&fit=crop',  # Coffee news
            'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400&h=300&fit=crop',  # Coffee beans
            'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&h=300&fit=crop',  # Coffee cherries
        ]
    }
    
    print("\n" + "=" * 80)
    print("IMAGE LIBRARY BY CATEGORY")
    print("=" * 80 + "\n")
    
    for category, images in image_library.items():
        print(f"📁 {category}:")
        for idx, img in enumerate(images, 1):
            print(f"   {idx}. {img}")
        print()
    
    return image_library


def fix_news_images_in_html(html_file_path, dry_run=True):
    """Fix missing or broken images in news items"""
    
    print("\n" + "=" * 80)
    print("FIX NEWS IMAGES")
    print("=" * 80 + "\n")
    
    if not os.path.exists(html_file_path):
        print(f"❌ Error: File not found: {html_file_path}")
        return
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original file
    if not dry_run:
        backup_path = html_file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backup created: {backup_path}\n")
    
    # Get image library
    image_library = suggest_images_for_categories()
    
    # Find all news items
    news_pattern = r'(<article class="news-item">)(.*?)(</article>)'
    
    fixes_applied = 0
    
    def fix_news_item(match):
        nonlocal fixes_applied
        opening_tag = match.group(1)
        item_content = match.group(2)
        closing_tag = match.group(3)
        
        # Check if news-thumbnail exists
        if '<div class="news-thumbnail">' not in item_content:
            # Extract category
            category_match = re.search(r'<div class="news-category[^"]*">(.*?)</div>', item_content)
            category = category_match.group(1) if category_match else "TIN TỨC"
            
            # Get appropriate image
            images = image_library.get(category, image_library['TIN TỨC'])
            img_url = images[0]
            
            # Add news-thumbnail div after opening article tag
            thumbnail_html = f'''
                        <div class="news-thumbnail">
                            <img src="{img_url}" alt="Coffee news image">
                            <div class="news-category technology">{category}</div>
                        </div>'''
            
            # Insert thumbnail before news-item-content
            if '<div class="news-item-content">' in item_content:
                item_content = item_content.replace(
                    '<div class="news-item-content">',
                    thumbnail_html + '\n                        <div class="news-item-content">'
                )
                fixes_applied += 1
                print(f"✅ Fixed: Added thumbnail for category '{category}'")
        
        # Check if img tag exists within thumbnail
        elif '<div class="news-thumbnail">' in item_content and '<img' not in item_content:
            # Extract category
            category_match = re.search(r'<div class="news-category[^"]*">(.*?)</div>', item_content)
            category = category_match.group(1) if category_match else "TIN TỨC"
            
            # Get appropriate image
            images = image_library.get(category, image_library['TIN TỨC'])
            img_url = images[0]
            
            # Add img tag inside news-thumbnail
            img_tag = f'\n                            <img src="{img_url}" alt="Coffee news image">'
            
            item_content = item_content.replace(
                '<div class="news-thumbnail">',
                f'<div class="news-thumbnail">{img_tag}'
            )
            fixes_applied += 1
            print(f"✅ Fixed: Added image for category '{category}'")
        
        return opening_tag + item_content + closing_tag
    
    # Apply fixes
    new_content = re.sub(news_pattern, fix_news_item, content, flags=re.DOTALL)
    
    if dry_run:
        print(f"\n🔍 DRY RUN: {fixes_applied} fixes would be applied")
        print("Run with dry_run=False to apply changes")
    else:
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"\n✅ Applied {fixes_applied} fixes to {html_file_path}")
    
    return fixes_applied


if __name__ == "__main__":
    # Path to index.html
    html_path = Path(__file__).parent.parent / 'web' / 'templates' / 'index.html'
    
    print("🔍 Step 1: Checking for issues...")
    issues = check_news_images(str(html_path))
    
    print("\n📚 Step 2: Image library...")
    suggest_images_for_categories()
    
    if issues:
        print("\n🔧 Step 3: Applying fixes (DRY RUN)...")
        fix_news_images_in_html(str(html_path), dry_run=True)
        
        print("\n" + "=" * 80)
        response = input("\nDo you want to apply these fixes? (yes/no): ").strip().lower()
        
        if response == 'yes':
            print("\n🔧 Applying fixes...")
            fix_news_images_in_html(str(html_path), dry_run=False)
            print("\n✅ Done! Please refresh your browser to see the changes.")
        else:
            print("\n❌ Fixes not applied. Exiting...")
    else:
        print("\n✅ No fixes needed!")
