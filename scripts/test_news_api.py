#!/usr/bin/env python3
"""
Test script to check news API and validate images
"""

import requests
import sys
from pathlib import Path

def test_news_api():
    """Test the news API endpoint"""
    
    api_url = "http://localhost:5000/api/news"
    
    print("=" * 80)
    print("NEWS API TESTER")
    print("=" * 80)
    print(f"\n🔍 Testing API: {api_url}\n")
    
    try:
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ API returned error: {data.get('error', 'Unknown error')}")
            return False
        
        articles = data.get('data', [])
        count = data.get('count', 0)
        
        print(f"✅ API Response successful")
        print(f"📰 Found {count} articles\n")
        
        # Check each article
        issues = []
        for idx, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            url = article.get('url', 'No URL')
            image = article.get('image', 'No image')
            source = article.get('source', 'No source')
            time = article.get('time', 'No time')
            
            print(f"📄 Article {idx}:")
            print(f"   Title: {title[:60]}...")
            print(f"   Source: {source}")
            print(f"   Time: {time}")
            print(f"   URL: {url[:60]}...")
            
            # Validate image
            if not image or image == 'No image':
                print(f"   ❌ ERROR: Missing image!")
                issues.append({'article': idx, 'issue': 'missing_image', 'title': title})
            elif not (image.startswith('http://') or image.startswith('https://')):
                print(f"   ⚠️  WARNING: Invalid image URL: {image}")
                issues.append({'article': idx, 'issue': 'invalid_url', 'title': title, 'image': image})
            elif 'unsplash.com' in image:
                print(f"   ✅ Image: Fallback (Unsplash)")
            else:
                print(f"   ✅ Image: {image[:60]}...")
            
            print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if not issues:
            print("✅ All articles have valid images!")
            return True
        else:
            print(f"⚠️  Found {len(issues)} issues:\n")
            for issue in issues:
                print(f"  - Article {issue['article']}: {issue['title'][:50]}...")
                print(f"    Issue: {issue['issue']}")
                if 'image' in issue:
                    print(f"    Image: {issue['image']}")
                print()
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to API")
        print("   Make sure Flask server is running:")
        print("   > cd coffee-export-project")
        print("   > python web/backend/api.py")
        return False
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_image_loading():
    """Test if images can be loaded"""
    
    print("\n" + "=" * 80)
    print("IMAGE LOADING TEST")
    print("=" * 80 + "\n")
    
    test_images = [
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=300&fit=crop&q=80",
        "https://photo-baomoi.bmcdn.me/example.jpg",  # Example Baomoi URL
    ]
    
    for idx, url in enumerate(test_images, 1):
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            status = response.status_code
            
            if status == 200:
                print(f"✅ Image {idx}: OK - {url[:60]}...")
            else:
                print(f"⚠️  Image {idx}: Status {status} - {url[:60]}...")
        
        except Exception as e:
            print(f"❌ Image {idx}: FAILED - {str(e)}")
    
    print()


if __name__ == "__main__":
    print("🚀 Starting News API Tests...\n")
    
    # Test 1: API functionality
    api_ok = test_news_api()
    
    # Test 2: Image loading
    test_image_loading()
    
    # Final result
    print("=" * 80)
    if api_ok:
        print("✅ ALL TESTS PASSED")
    else:
        print("⚠️  SOME ISSUES FOUND - Please check the output above")
    print("=" * 80)
    
    sys.exit(0 if api_ok else 1)
