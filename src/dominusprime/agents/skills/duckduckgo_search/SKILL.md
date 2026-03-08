---
metadata: { "dominusprime": { "emoji": "🔍" } }
---

# DuckDuckGo Search Skill

Comprehensive web search and research capability using DuckDuckGo's privacy-focused search engine. This skill enables DominusPrime to search the internet, gather information, and provide up-to-date answers without tracking or profiling.

## Overview

This skill provides:
- 🔍 **Web Search**: Search the internet for any topic
- 📰 **News Search**: Find recent news articles
- 🖼️ **Image Search**: Search for images
- 🎥 **Video Search**: Find videos from various platforms
- 🗺️ **Maps/Places**: Search for locations and places
- 💡 **Instant Answers**: Get quick facts and definitions
- 🌐 **Privacy-First**: No tracking, no profiling, no search history

## Installation

### Install the DuckDuckGo Search Library

```bash
pip3 install duckduckgo-search
```

Or add to your project's requirements:

```bash
# requirements.txt
duckduckgo-search>=4.0.0
```

### Verify Installation

```python
from duckduckgo_search import DDGS

# Test basic search
with DDGS() as ddgs:
    results = list(ddgs.text("Python programming", max_results=5))
    print(f"Found {len(results)} results")
```

## Usage Examples

### 1. Basic Text Search

```python
from duckduckgo_search import DDGS

def search_web(query, max_results=10):
    """Search DuckDuckGo for text results"""
    with DDGS() as ddgs:
        results = list(ddgs.text(
            keywords=query,
            max_results=max_results
        ))
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['href']}")
        print(f"   {result['body']}\n")
    
    return results

# Usage
results = search_web("artificial intelligence trends 2026", max_results=5)
```

**Output Fields:**
- `title`: Page title
- `href`: URL
- `body`: Snippet/description

### 2. News Search

```python
def search_news(query, max_results=10):
    """Search for recent news articles"""
    with DDGS() as ddgs:
        news_results = list(ddgs.news(
            keywords=query,
            max_results=max_results
        ))
    
    for article in news_results:
        print(f"📰 {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Date: {article['date']}")
        print(f"   URL: {article['url']}")
        print(f"   {article['body']}\n")
    
    return news_results

# Usage
news = search_news("climate change", max_results=5)
```

**Output Fields:**
- `title`: Article title
- `url`: Article URL
- `source`: News source
- `date`: Publication date
- `body`: Article snippet

### 3. Image Search

```python
def search_images(query, max_results=20):
    """Search for images"""
    with DDGS() as ddgs:
        images = list(ddgs.images(
            keywords=query,
            max_results=max_results
        ))
    
    for img in images:
        print(f"🖼️  {img['title']}")
        print(f"   Image: {img['image']}")
        print(f"   Thumbnail: {img['thumbnail']}")
        print(f"   Source: {img['source']}\n")
    
    return images

# Usage
images = search_images("python logo", max_results=10)
```

**Output Fields:**
- `title`: Image title
- `image`: Full-size image URL
- `thumbnail`: Thumbnail URL
- `source`: Source website
- `width`: Image width
- `height`: Image height

### 4. Video Search

```python
def search_videos(query, max_results=10):
    """Search for videos"""
    with DDGS() as ddgs:
        videos = list(ddgs.videos(
            keywords=query,
            max_results=max_results
        ))
    
    for video in videos:
        print(f"🎥 {video['title']}")
        print(f"   URL: {video['content']}")
        print(f"   Duration: {video.get('duration', 'N/A')}")
        print(f"   Publisher: {video.get('publisher', 'N/A')}\n")
    
    return videos

# Usage
videos = search_videos("Python tutorial", max_results=5)
```

**Output Fields:**
- `title`: Video title
- `content`: Video URL
- `description`: Video description
- `duration`: Video length
- `publisher`: Video publisher
- `published`: Publication date

### 5. Instant Answers

```python
def get_instant_answer(query):
    """Get instant answers for factual queries"""
    with DDGS() as ddgs:
        answer = ddgs.answers(keywords=query)
    
    if answer:
        for item in answer:
            print(f"💡 {item.get('text', '')}")
            if 'url' in item:
                print(f"   Source: {item['url']}")
    else:
        print("No instant answer found")
    
    return answer

# Usage
answer = get_instant_answer("What is the capital of France?")
```

### 6. Advanced Text Search with Filters

```python
def advanced_search(query, region='wt-wt', safesearch='moderate', timelimit=None):
    """
    Advanced search with filters
    
    Args:
        query: Search keywords
        region: Region code (e.g., 'us-en', 'uk-en', 'wt-wt' for worldwide)
        safesearch: 'on', 'moderate', or 'off'
        timelimit: 'd' (day), 'w' (week), 'm' (month), 'y' (year)
    """
    with DDGS() as ddgs:
        results = list(ddgs.text(
            keywords=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=10
        ))
    
    return results

# Search for recent results
recent_results = advanced_search(
    "AI breakthroughs",
    region='us-en',
    timelimit='w'  # Past week only
)
```

### 7. Suggestions/Autocomplete

```python
def get_suggestions(query):
    """Get search suggestions"""
    with DDGS() as ddgs:
        suggestions = list(ddgs.suggestions(keywords=query))
    
    print(f"💭 Suggestions for '{query}':")
    for suggestion in suggestions:
        print(f"   - {suggestion['phrase']}")
    
    return suggestions

# Usage
suggestions = get_suggestions("machine learning")
```

### 8. Maps/Places Search

```python
def search_places(query, place=None, max_results=10):
    """Search for places/locations"""
    with DDGS() as ddgs:
        places = list(ddgs.maps(
            keywords=query,
            place=place,
            max_results=max_results
        ))
    
    for p in places:
        print(f"📍 {p.get('title', 'N/A')}")
        print(f"   Address: {p.get('address', 'N/A')}")
        print(f"   Phone: {p.get('phone', 'N/A')}")
        print(f"   Hours: {p.get('hours', 'N/A')}")
        if 'latitude' in p and 'longitude' in p:
            print(f"   Location: {p['latitude']}, {p['longitude']}")
        print()
    
    return places

# Usage
places = search_places("coffee shops", place="San Francisco")
```

## Complete API Reference

### DDGS Class Methods

#### `text(keywords, region='wt-wt', safesearch='moderate', timelimit=None, max_results=None)`
Search for text results.

**Parameters:**
- `keywords` (str): Search query
- `region` (str): Region code (default: 'wt-wt' for worldwide)
  - Examples: 'us-en', 'uk-en', 'de-de', 'fr-fr', 'es-es'
- `safesearch` (str): Safe search setting
  - Options: 'on', 'moderate', 'off' (default: 'moderate')
- `timelimit` (str): Time filter
  - Options: 'd' (day), 'w' (week), 'm' (month), 'y' (year)
- `max_results` (int): Maximum number of results

**Returns:** List of dictionaries with keys: `title`, `href`, `body`

#### `news(keywords, region='wt-wt', safesearch='moderate', timelimit=None, max_results=None)`
Search for news articles.

**Parameters:** Same as `text()`

**Returns:** List of dictionaries with keys: `title`, `url`, `source`, `date`, `body`, `image`

#### `images(keywords, region='wt-wt', safesearch='moderate', size=None, color=None, type_image=None, layout=None, license_image=None, max_results=None)`
Search for images.

**Additional Parameters:**
- `size`: Image size filter
  - Options: 'Small', 'Medium', 'Large', 'Wallpaper'
- `color`: Color filter
  - Options: 'color', 'Monochrome', 'Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple', 'Pink', 'Brown', 'Black', 'Gray', 'Teal', 'White'
- `type_image`: Image type
  - Options: 'photo', 'clipart', 'gif', 'transparent', 'line'
- `layout`: Image layout
  - Options: 'Square', 'Tall', 'Wide'
- `license_image`: License type
  - Options: 'any', 'Public', 'Share', 'Modify', 'ModifyCommercially'

**Returns:** List of dictionaries with keys: `title`, `image`, `thumbnail`, `url`, `height`, `width`, `source`

#### `videos(keywords, region='wt-wt', safesearch='moderate', timelimit=None, resolution=None, duration=None, license_videos=None, max_results=None)`
Search for videos.

**Additional Parameters:**
- `resolution`: Video resolution
  - Options: 'high', 'standard'
- `duration`: Video duration
  - Options: 'short', 'medium', 'long'
- `license_videos`: License type
  - Options: 'creativeCommon', 'youtube'

**Returns:** List of dictionaries with keys: `title`, `content`, `description`, `duration`, `published`, `publisher`, `uploader`

#### `maps(keywords, place=None, street=None, city=None, county=None, state=None, country=None, postalcode=None, latitude=None, longitude=None, radius=0, max_results=None)`
Search for places/locations.

**Parameters:**
- `keywords` (str): Search query
- `place` (str): Place name for context
- `street`, `city`, `county`, `state`, `country`, `postalcode`: Location filters
- `latitude`, `longitude`: Coordinates
- `radius` (int): Search radius in km

**Returns:** List of dictionaries with location details

#### `answers(keywords)`
Get instant answers for factual queries.

**Parameters:**
- `keywords` (str): Query

**Returns:** List of answer dictionaries

#### `suggestions(keywords, region='wt-wt')`
Get search suggestions/autocomplete.

**Parameters:**
- `keywords` (str): Partial query
- `region` (str): Region code

**Returns:** List of suggestion dictionaries with `phrase` key

## Practical Workflows

### Workflow 1: Research Assistant

```python
def research_topic(topic, max_results=10):
    """Comprehensive research on a topic"""
    print(f"🔍 Researching: {topic}\n")
    
    with DDGS() as ddgs:
        # Get instant answer
        print("💡 Quick Answer:")
        answers = ddgs.answers(keywords=topic)
        if answers:
            for ans in answers[:1]:
                print(f"   {ans.get('text', '')}\n")
        
        # Get web results
        print("📄 Top Search Results:")
        web_results = list(ddgs.text(topic, max_results=max_results))
        for i, result in enumerate(web_results[:5], 1):
            print(f"{i}. {result['title']}")
            print(f"   {result['href']}")
            print(f"   {result['body'][:150]}...\n")
        
        # Get recent news
        print("📰 Recent News:")
        news = list(ddgs.news(topic, max_results=5))
        for article in news:
            print(f"• {article['title']} ({article['date']})")
            print(f"  {article['url']}\n")
        
        return {
            'answers': answers,
            'web_results': web_results,
            'news': news
        }

# Usage
research = research_topic("quantum computing")
```

### Workflow 2: Fact Checker

```python
def verify_claim(claim):
    """Search for information to verify a claim"""
    with DDGS() as ddgs:
        # Search for the claim
        results = list(ddgs.text(claim, max_results=10))
        
        # Search for fact-checking sites
        fact_check_query = f"{claim} fact check site:snopes.com OR site:factcheck.org"
        fact_checks = list(ddgs.text(fact_check_query, max_results=5))
        
        return {
            'general_results': results,
            'fact_checks': fact_checks
        }

# Usage
verification = verify_claim("coffee is good for health")
```

### Workflow 3: Competitive Research

```python
def analyze_competitors(company_name):
    """Gather information about a company and competitors"""
    with DDGS() as ddgs:
        # Company info
        company_info = list(ddgs.text(f"{company_name} company", max_results=5))
        
        # Recent news
        company_news = list(ddgs.news(company_name, timelimit='m', max_results=10))
        
        # Competitors
        competitor_query = f"{company_name} competitors alternatives"
        competitors = list(ddgs.text(competitor_query, max_results=10))
        
        return {
            'info': company_info,
            'news': company_news,
            'competitors': competitors
        }

# Usage
analysis = analyze_competitors("OpenAI")
```

### Workflow 4: Content Aggregator

```python
def aggregate_content(topic, include_images=True, include_videos=True):
    """Aggregate various content types for a topic"""
    content = {}
    
    with DDGS() as ddgs:
        # Text results
        content['articles'] = list(ddgs.text(topic, max_results=10))
        
        # News
        content['news'] = list(ddgs.news(topic, max_results=10))
        
        # Images
        if include_images:
            content['images'] = list(ddgs.images(topic, max_results=20))
        
        # Videos
        if include_videos:
            content['videos'] = list(ddgs.videos(topic, max_results=10))
    
    return content

# Usage
content = aggregate_content("sustainable energy")
```

### Workflow 5: Location-Based Search

```python
def find_local_services(service, location):
    """Find local services in a specific area"""
    with DDGS() as ddgs:
        # Search for places
        places = list(ddgs.maps(
            keywords=service,
            place=location,
            max_results=15
        ))
        
        # Search for reviews/articles
        query = f"{service} in {location} reviews"
        reviews = list(ddgs.text(query, max_results=5))
        
        return {
            'places': places,
            'reviews': reviews
        }

# Usage
services = find_local_services("dentist", "Boston, MA")
```

## Best Practices

### 1. Rate Limiting and Throttling

```python
import time
from functools import wraps

def rate_limit(delay=1.0):
    """Decorator to add delay between searches"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            time.sleep(delay)
            return result
        return wrapper
    return decorator

@rate_limit(delay=1.5)
def search_with_delay(query):
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=10))
```

### 2. Error Handling

```python
def safe_search(query, search_type='text', max_results=10):
    """Search with comprehensive error handling"""
    try:
        with DDGS() as ddgs:
            if search_type == 'text':
                results = list(ddgs.text(query, max_results=max_results))
            elif search_type == 'news':
                results = list(ddgs.news(query, max_results=max_results))
            elif search_type == 'images':
                results = list(ddgs.images(query, max_results=max_results))
            elif search_type == 'videos':
                results = list(ddgs.videos(query, max_results=max_results))
            else:
                raise ValueError(f"Unknown search type: {search_type}")
            
            return {'success': True, 'results': results}
    
    except Exception as e:
        print(f"Search error: {e}")
        return {'success': False, 'error': str(e), 'results': []}

# Usage
result = safe_search("Python programming", search_type='text')
if result['success']:
    print(f"Found {len(result['results'])} results")
```

### 3. Result Caching

```python
import json
import hashlib
from pathlib import Path

class SearchCache:
    def __init__(self, cache_dir='.search_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, query, search_type):
        key_str = f"{query}:{search_type}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, query, search_type):
        key = self._get_cache_key(query, search_type)
        cache_file = self.cache_dir / f"{key}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def set(self, query, search_type, results):
        key = self._get_cache_key(query, search_type)
        cache_file = self.cache_dir / f"{key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(results, f)

# Usage
cache = SearchCache()

def cached_search(query, search_type='text', max_results=10):
    # Check cache first
    cached = cache.get(query, search_type)
    if cached:
        print("Using cached results")
        return cached
    
    # Perform search
    with DDGS() as ddgs:
        if search_type == 'text':
            results = list(ddgs.text(query, max_results=max_results))
        # ... other types
        
        # Cache results
        cache.set(query, search_type, results)
        return results
```

### 4. Result Formatting

```python
def format_search_results(results, format_type='plain'):
    """Format search results for different outputs"""
    if format_type == 'plain':
        output = []
        for i, r in enumerate(results, 1):
            output.append(f"{i}. {r['title']}")
            output.append(f"   {r['href']}")
            output.append(f"   {r['body']}\n")
        return '\n'.join(output)
    
    elif format_type == 'markdown':
        output = []
        for r in results:
            output.append(f"### [{r['title']}]({r['href']})")
            output.append(f"{r['body']}\n")
        return '\n'.join(output)
    
    elif format_type == 'html':
        output = ['<div class="search-results">']
        for r in results:
            output.append(f'  <div class="result">')
            output.append(f'    <h3><a href="{r["href"]}">{r["title"]}</a></h3>')
            output.append(f'    <p>{r["body"]}</p>')
            output.append(f'  </div>')
        output.append('</div>')
        return '\n'.join(output)
    
    return results
```

### 5. Query Optimization

```python
def optimize_query(query, search_type='text'):
    """Optimize search queries for better results"""
    optimizations = {
        'text': query,
        'news': query,
        'images': query,
        'videos': query
    }
    
    # Remove common stop words for better results
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
    words = query.lower().split()
    filtered = [w for w in words if w not in stop_words]
    
    # Add quotes for exact phrases if multiple words
    if len(filtered) > 1 and search_type == 'text':
        optimizations['text'] = f'"{" ".join(filtered)}"'
    
    return optimizations.get(search_type, query)
```

## Region Codes

Common region codes for localized search:

- `wt-wt` - Worldwide (default)
- `us-en` - United States
- `uk-en` - United Kingdom
- `ca-en` - Canada (English)
- `au-en` - Australia
- `de-de` - Germany
- `fr-fr` - France
- `es-es` - Spain
- `it-it` - Italy
- `nl-nl` - Netherlands
- `pl-pl` - Poland
- `br-pt` - Brazil
- `mx-es` - Mexico
- `cn-zh` - China
- `jp-jp` - Japan
- `kr-kr` - South Korea
- `in-en` - India
- `za-en` - South Africa

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'duckduckgo_search'`
- **Solution**: Install the library: `pip3 install duckduckgo-search`

**Issue**: Empty results returned
- **Solution**: Try different keywords, check your internet connection, or adjust filters

**Issue**: Rate limiting errors
- **Solution**: Add delays between requests, implement exponential backoff

**Issue**: Timeout errors
- **Solution**: Reduce `max_results`, check network connection, or add timeout handling

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Now run searches to see detailed output
with DDGS() as ddgs:
    results = list(ddgs.text("test query", max_results=5))
```

## Privacy & Security

### Why DuckDuckGo?

- ✅ **No tracking**: DuckDuckGo doesn't track or profile users
- ✅ **No search history**: Searches are not stored or associated with users
- ✅ **Privacy by default**: Safe search and privacy protection built-in
- ✅ **No filter bubble**: Same results for everyone, no personalization
- ✅ **Open source library**: Community-maintained Python library

### Security Best Practices

1. **Validate Input**: Always sanitize user queries before searching
2. **Rate Limiting**: Don't overwhelm the service with requests
3. **Error Handling**: Gracefully handle network errors and timeouts
4. **Result Filtering**: Validate and sanitize results before displaying
5. **HTTPS Only**: All DuckDuckGo searches use encrypted connections

## Integration with DominusPrime

### Skill Commands

When using this skill, DominusPrime can help you:

- 🔍 **Search**: "Search the web for AI trends 2026"
- 📰 **News**: "Find recent news about climate change"
- 🖼️ **Images**: "Search for images of the Eiffel Tower"
- 🎥 **Videos**: "Find Python tutorial videos"
- 📍 **Places**: "Find coffee shops in New York"
- 💡 **Answer**: "What is quantum computing?"
- 🔬 **Research**: "Research the history of artificial intelligence"

### Example Integration

```python
class DuckDuckGoSearchSkill:
    """DominusPrime skill for web search"""
    
    def __init__(self):
        self.ddgs = None
    
    def search(self, query, search_type='text', max_results=10, **kwargs):
        """Universal search method"""
        with DDGS() as ddgs:
            if search_type == 'text':
                return list(ddgs.text(query, max_results=max_results, **kwargs))
            elif search_type == 'news':
                return list(ddgs.news(query, max_results=max_results, **kwargs))
            elif search_type == 'images':
                return list(ddgs.images(query, max_results=max_results, **kwargs))
            elif search_type == 'videos':
                return list(ddgs.videos(query, max_results=max_results, **kwargs))
            elif search_type == 'maps':
                return list(ddgs.maps(query, max_results=max_results, **kwargs))
            else:
                raise ValueError(f"Unknown search type: {search_type}")
    
    def quick_answer(self, query):
        """Get instant answer"""
        with DDGS() as ddgs:
            return ddgs.answers(query)
```

## Resources

- **Library Repository**: https://github.com/deedy5/duckduckgo_search
- **DuckDuckGo**: https://duckduckgo.com
- **Privacy Policy**: https://duckduckgo.com/privacy
- **API Documentation**: See library docs for latest updates

---

**Skill Version**: 1.0.0  
**Last Updated**: 2026-03-08  
**Library**: duckduckgo-search >= 4.0.0  
**Maintained by**: QuantaNova Development Team
