"""
News Crawler Module - Clean and Modular
Crawl coffee news from multiple sources and sort by time
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional
import random


class NewsCrawler:
    """Base class for news crawlers"""
    
    FALLBACK_IMAGES = [
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1578632292335-df3abbb0d586?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1587734195503-904fca47ad4b?w=400&h=300&fit=crop&q=80",
    ]
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def validate_image_url(self, url: Optional[str]) -> Optional[str]:
        """Validate and clean image URL"""
        if not url:
            return None
        
        # Remove data URLs and placeholders
        if url.startswith('data:') or 'placeholder' in url.lower():
            return None
        
        # Ensure HTTP/HTTPS
        if not (url.startswith('http://') or url.startswith('https://')):
            return None
        
        return url
    
    def get_fallback_image(self) -> str:
        """Get random fallback image"""
        return random.choice(self.FALLBACK_IMAGES)
    
    def parse_relative_time(self, time_str: str) -> datetime:
        """Parse relative time strings like '2 giờ trước', '1 ngày trước'"""
        now = datetime.now()
        time_str = time_str.lower().strip()
        
        # Patterns for Vietnamese time
        patterns = [
            (r'(\d+)\s*phút', 'minutes'),
            (r'(\d+)\s*giờ', 'hours'),
            (r'(\d+)\s*ngày', 'days'),
            (r'(\d+)\s*tuần', 'weeks'),
            (r'(\d+)\s*tháng', 'months'),
        ]
        
        for pattern, unit in patterns:
            match = re.search(pattern, time_str)
            if match:
                value = int(match.group(1))
                if unit == 'minutes':
                    return now - timedelta(minutes=value)
                elif unit == 'hours':
                    return now - timedelta(hours=value)
                elif unit == 'days':
                    return now - timedelta(days=value)
                elif unit == 'weeks':
                    return now - timedelta(weeks=value)
                elif unit == 'months':
                    return now - timedelta(days=value * 30)
        
        return now
    
    def crawl(self) -> List[Dict]:
        """Override this method in child classes"""
        raise NotImplementedError


class BaoMoiCrawler(NewsCrawler):
    """Crawler for Baomoi.com"""
    
    def crawl(self) -> List[Dict]:
        """Crawl news from Baomoi.com"""
        try:
            url = "https://baomoi.com/tim-kiem/gi%C3%A1%20c%C3%A0%20ph%C3%AA.epi"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            articles = []
            for card in soup.select("div.bm-card"):
                article = self._parse_article(card)
                if article:
                    articles.append(article)
            
            return articles[:12]  # Return top 12 articles
        
        except Exception as e:
            print(f"Error crawling Baomoi: {e}")
            return []
    
    def _parse_article(self, card) -> Optional[Dict]:
        """Parse a single article card"""
        # Title and URL
        a_tag = card.select_one("a[title]")
        if not a_tag:
            return None
        
        title = a_tag.get("title", "").strip()
        href = a_tag.get("href", "")
        link = f"https://baomoi.com{href}" if href.startswith("/") else href
        
        # Image
        image = self._extract_image(card)
        
        # Source
        source_tag = card.select_one(".bm-card-source")
        source = source_tag.get("title") if source_tag else "Báo Mới"
        
        # Time
        time_tag = card.select_one("time")
        time_str = time_tag.get_text(strip=True) if time_tag else ""
        timestamp = self.parse_relative_time(time_str)
        
        return {
            "title": title,
            "url": link,
            "image": image,
            "source": source,
            "time": time_str,
            "timestamp": timestamp.isoformat(),
            "published_date": timestamp
        }
    
    def _extract_image(self, card) -> str:
        """Extract image URL with multiple fallback strategies"""
        # Try <img src> or <img data-src>
        img_tag = card.select_one("img")
        if img_tag:
            img_url = img_tag.get("src") or img_tag.get("data-src")
            validated = self.validate_image_url(img_url)
            if validated:
                return validated
        
        # Try <source srcset>
        source_tag = card.select_one("source[srcset], source[data-srcset]")
        if source_tag:
            srcset = source_tag.get("srcset") or source_tag.get("data-srcset")
            if srcset:
                img_url = srcset.split()[0].split(',')[0].strip()
                validated = self.validate_image_url(img_url)
                if validated:
                    return validated
        
        # Try regex search
        match = re.search(r"https://photo-baomoi\.bmcdn\.me/[^\s\"']+\.(jpg|webp|avif|png)", str(card))
        if match:
            validated = self.validate_image_url(match.group(0))
            if validated:
                return validated
        
        # Fallback
        return self.get_fallback_image()


class VOVCrawler(NewsCrawler):
    """Crawler for VOV.vn (Voice of Vietnam)"""
    
    def crawl(self) -> List[Dict]:
        """Crawl news from VOV.vn"""
        try:
            url = "https://vov.vn/thi-truong/gia-ca-phe"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            articles = []
            
            # VOV structure: Find all links with substantial text (likely articles)
            all_links = soup.select("a[href]")
            
            for link in all_links:
                text = link.get_text(strip=True)
                href = link.get("href", "")
                
                # Filter: Must have meaningful text and coffee-related href
                if (len(text) > 30 and 
                    href and 
                    ('ca-phe' in href.lower() or 'gia' in href.lower())):
                    
                    article = self._parse_article_from_link(link, soup)
                    if article:
                        articles.append(article)
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            return unique_articles[:12]
        
        except Exception as e:
            print(f"Error crawling VOV: {e}")
            return []
    
    def _parse_date_from_title(self, title: str) -> datetime:
        """
        Parse date from VOV article title
        VOV format: "Giá cà phê hôm nay DD/MM: ..."
        Example: "Giá cà phê hôm nay 13/11: Cà phê trong nước..."
        """
        # Try to extract DD/MM pattern from title
        date_pattern = r'(\d{1,2})/(\d{1,2})'
        match = re.search(date_pattern, title)
        
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            
            # Assume current year
            current_year = datetime.now().year
            
            try:
                # Create datetime object
                parsed_date = datetime(current_year, month, day)
                
                # If date is in the future (e.g., we're in Dec and article is from Jan)
                # it's probably from last year
                if parsed_date > datetime.now():
                    parsed_date = datetime(current_year - 1, month, day)
                
                return parsed_date
            except ValueError:
                # Invalid date, return now
                return datetime.now()
        
        # If no date pattern found, return current time
        return datetime.now()
    
    def _parse_article_from_link(self, link, soup) -> Optional[Dict]:
        """Parse article from a link element"""
        # Get title from link text or parent context
        title = link.get_text(strip=True)
        if not title or len(title) < 20:
            return None
        
        # Get URL
        href = link.get("href", "")
        if href.startswith("/"):
            url = f"https://vov.vn{href}"
        elif not href.startswith("http"):
            return None
        else:
            url = href
        
        # Find image - check parent elements
        image = None
        parent = link.parent
        for _ in range(3):  # Check up to 3 levels up
            if parent:
                img_tag = parent.select_one("img")
                if img_tag:
                    image = img_tag.get("src") or img_tag.get("data-src")
                    if image and image.startswith("/"):
                        image = f"https://vov.vn{image}"
                    break
                parent = parent.parent
        
        # Validate image or use fallback
        validated_image = self.validate_image_url(image)
        if not validated_image:
            validated_image = self.get_fallback_image()
        
        # Parse time from title (VOV format: "Giá cà phê hôm nay 13/11")
        timestamp = self._parse_date_from_title(title)
        
        # Format time display
        time_str = timestamp.strftime("%d/%m/%Y")
        
        return {
            "title": title,
            "url": url,
            "image": validated_image,
            "source": "VOV",
            "time": time_str,
            "timestamp": timestamp.isoformat(),
            "published_date": timestamp
        }


class VnExpressCrawler(NewsCrawler):
    """Crawler for VnExpress.net"""
    
    def crawl(self) -> List[Dict]:
        """Crawl news from VnExpress"""
        try:
            url = "https://vnexpress.net/tim-kiem?q=gi%C3%A1+c%C3%A0+ph%C3%AA"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            articles = []
            for article in soup.select("article.item-news"):
                parsed = self._parse_article(article)
                if parsed:
                    articles.append(parsed)
            
            return articles[:12]
        
        except Exception as e:
            print(f"Error crawling VnExpress: {e}")
            return []
    
    def _parse_article(self, article) -> Optional[Dict]:
        """Parse VnExpress article"""
        # Title and URL
        title_tag = article.select_one("h3.title-news a, h2.title-news a")
        if not title_tag:
            return None
        
        title = title_tag.get("title", title_tag.get_text(strip=True))
        link = title_tag.get("href", "")
        
        # Image
        img_tag = article.select_one("img")
        image = self.validate_image_url(img_tag.get("src") if img_tag else None)
        if not image:
            image = self.get_fallback_image()
        
        # Time
        time_tag = article.select_one("span.time")
        time_str = time_tag.get_text(strip=True) if time_tag else ""
        timestamp = self.parse_relative_time(time_str)
        
        return {
            "title": title,
            "url": link,
            "image": image,
            "source": "VnExpress",
            "time": time_str,
            "timestamp": timestamp.isoformat(),
            "published_date": timestamp
        }


class CafeControlCrawler(NewsCrawler):
    """Crawler for CafeControl - Vietnamese coffee news site"""
    
    def crawl(self) -> List[Dict]:
        """Crawl news from CafeControl"""
        try:
            url = "https://cafecontrol.vn/tin-tuc"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            articles = []
            for article in soup.select("article, .post-item, .news-item"):
                parsed = self._parse_article(article)
                if parsed:
                    articles.append(parsed)
            
            return articles[:12]
        
        except Exception as e:
            print(f"Error crawling CafeControl: {e}")
            return []
    
    def _parse_article(self, article) -> Optional[Dict]:
        """Parse CafeControl article"""
        # Title and URL
        title_tag = article.select_one("h2 a, h3 a, .title a")
        if not title_tag:
            return None
        
        title = title_tag.get_text(strip=True)
        link = title_tag.get("href", "")
        if link and not link.startswith("http"):
            link = f"https://cafecontrol.vn{link}"
        
        # Image
        img_tag = article.select_one("img")
        image = self.validate_image_url(img_tag.get("src") if img_tag else None)
        if not image:
            image = self.get_fallback_image()
        
        # Time - assume recent
        timestamp = datetime.now()
        
        return {
            "title": title,
            "url": link,
            "image": image,
            "source": "CafeControl",
            "time": "Mới đây",
            "timestamp": timestamp.isoformat(),
            "published_date": timestamp
        }


class NewsAggregator:
    """Aggregate news from multiple sources and sort by time"""
    
    def __init__(self):
        self.crawlers = [
            VOVCrawler(),          # Priority 1: VOV
            VnExpressCrawler(),    # Priority 2: VnExpress
            BaoMoiCrawler(),       # Priority 3: BaoMoi (fallback)
            # CafeControlCrawler(),  # Add more as needed
        ]
    
    def get_all_news(self, limit: int = 9) -> List[Dict]:
        """Get news from all sources, sort by time, and return top N"""
        all_articles = []
        
        # Crawl from all sources
        for crawler in self.crawlers:
            try:
                articles = crawler.crawl()
                all_articles.extend(articles)
            except Exception as e:
                print(f"Error with crawler {crawler.__class__.__name__}: {e}")
        
        # Sort by timestamp (newest first)
        all_articles.sort(key=lambda x: x.get('published_date', datetime.min), reverse=True)
        
        # Remove duplicates based on title similarity
        unique_articles = self._remove_duplicates(all_articles)
        
        # Return top N
        return unique_articles[:limit]
    
    def _remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title similarity"""
        unique = []
        seen_titles = set()
        
        for article in articles:
            # Normalize title for comparison
            title_normalized = re.sub(r'\s+', ' ', article['title'].lower()).strip()
            
            # Check if similar title exists
            is_duplicate = False
            for seen_title in seen_titles:
                # Simple similarity check - more than 80% overlap
                if self._similarity(title_normalized, seen_title) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(article)
                seen_titles.add(title_normalized)
        
        return unique
    
    def _similarity(self, str1: str, str2: str) -> float:
        """Calculate simple similarity between two strings"""
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
