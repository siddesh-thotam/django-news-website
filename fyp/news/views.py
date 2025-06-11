from django.shortcuts import render, redirect
import requests
from datetime import datetime, timedelta
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decouple import config
import json

@login_required
def index(request):
    
    today = datetime.now()
    from_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')  
    
    # Get category and country from request
    category = request.GET.get('category', 'general')
    country = request.GET.get('country', 'us')  # Default to US
    
    valid_categories = ['general', 'business', 'technology', 'health', 'science', 'sports', 'entertainment']
    
    # Define available countries with their codes
    valid_countries = {
        'us': 'United States',
        'in': 'India', 
        'gb': 'United Kingdom',
        'ca': 'Canada',
        'au': 'Australia',
        'de': 'Germany',
        'fr': 'France',
        'jp': 'Japan',
        'br': 'Brazil',
        'mx': 'Mexico',
        'za': 'South Africa',
        'ng': 'Nigeria',
        'eg': 'Egypt',
        'ae': 'UAE',
        'sg': 'Singapore'
    }
    
    if category not in valid_categories:
        category = 'general'
        
    if country not in valid_countries:
        country = 'us'
    
    # Check if we're requesting Indian news
    if country == 'in':
        return fetch_indian_news(request, category, valid_categories, valid_countries)
    else:
        return fetch_newsapi_news(request, category, country, valid_categories, valid_countries)

def fetch_indian_news(request, category, valid_categories, valid_countries):
    """Fetch Indian news using Mediastack API"""
    
    # Mediastack API key
    MEDIASTACK_API_KEY = "8c1e2f1fb162a63b876db026f93c3519"
    
    # Map categories to Mediastack categories
    category_mapping = {
        'general': 'general',
        'business': 'business',
        'technology': 'technology',
        'health': 'health',
        'science': 'science',
        'sports': 'sports',
        'entertainment': 'entertainment'
    }
    
    # Use the mapped category or default to general
    mediastack_category = category_mapping.get(category, 'general')
    
    # Construct Mediastack API URL for Indian news
    url = f"http://api.mediastack.com/v1/news?access_key={MEDIASTACK_API_KEY}&countries=in&categories={mediastack_category}&languages=en&limit=50&sort=published_desc"
    
    print(f"=== MEDIASTACK DEBUG INFO ===")
    print(f"Requested Country: India")
    print(f"Requested Category: {category}")
    print(f"Mediastack Category: {mediastack_category}")
    print(f"API URL: {url.replace(MEDIASTACK_API_KEY, 'HIDDEN_API_KEY')}")

    try:
        response = requests.get(url, timeout=15)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            error_message = f"Mediastack API returned status code {response.status_code}"
            
            if response.status_code == 401:
                error_message += " - Invalid API key"
            elif response.status_code == 429:
                error_message += " - API rate limit exceeded. Try again later."
            elif response.status_code == 422:
                error_message += " - Invalid request parameters"
            
            print(f"Mediastack API Error: {error_message}")
            raise requests.RequestException(error_message)
            
        news_data = response.json()
        
        print(f"Mediastack API Response Keys: {list(news_data.keys())}")
        
        # Check for API errors in response
        if 'error' in news_data:
            error_info = news_data['error']
            error_msg = f"Mediastack API Error: {error_info.get('message', 'Unknown error')}"
            print(f"API Error: {error_msg}")
            raise requests.RequestException(error_msg)
        
        # Check if 'data' exists in response (Mediastack uses 'data' instead of 'articles')
        if 'data' not in news_data:
            raise KeyError("No 'data' found in Mediastack API response")
            
        articles = news_data['data']
        
        print(f"Total articles from Mediastack: {len(articles)}")
        
        # Handle case where articles list is empty
        if not articles:
            print(f"No articles found for India, category={category}")
            context = {
                'success': True,
                'articles': [],
                'current_category': category,
                'current_country': 'in',
                'categories': valid_categories,
                'countries': valid_countries,
                'debug_info': {
                    'total_results': len(articles),
                    'api_status': 'success',
                    'country_name': 'India',
                    'no_articles_reason': f"No articles available for India in {category} category from Mediastack API"
                }
            }
            return render(request, 'fyp/index.html', context)
        
        processed_articles = []
        for i, article in enumerate(articles):
            if article:  # Make sure article is not None
                processed_article = {
                    'title': article.get('title', 'No title available'),
                    'description': article.get('description', 'No description available'),
                    'image': article.get('image', ''),  # Mediastack uses 'image' instead of 'urlToImage'
                    'url': article.get('url', '#'),  
                    'source': article.get('source', 'Unknown Source'),  # Mediastack has direct source field
                    'published_at': article.get('published_at', '')  # Mediastack uses 'published_at'
                }
                processed_articles.append(processed_article)
                
                # Debug first few articles
                if i < 3:
                    print(f"Indian Article {i+1}: {processed_article['title'][:50]}...")

        print(f"Successfully processed {len(processed_articles)} Indian articles")

        context = {
            'articles': processed_articles,
            'current_category': category,
            'current_country': 'in',
            'categories': valid_categories,
            'countries': valid_countries,
            'success': True,
            'debug_info': {
                'total_results': len(processed_articles),
                'api_status': 'success',
                'country_name': 'India',
                'articles_count': len(processed_articles),
                'api_used': 'Mediastack'
            }
        }
        
        return render(request, 'fyp/index.html', context)
        
    except requests.RequestException as e:
        print(f"Mediastack API Request Error: {str(e)}")
        context = {
            'success': False,
            'error': f"Failed to fetch Indian news: {str(e)}",
            'current_category': category,
            'current_country': 'in',
            'categories': valid_categories,
            'countries': valid_countries
        }
        return render(request, 'fyp/index.html', context)  
    except KeyError as e:
        print(f"Mediastack Data Error: {str(e)}")
        context = {
            'success': False,
            'error': f"Invalid Mediastack API response: {str(e)}",
            'current_category': category,
            'current_country': 'in',
            'categories': valid_categories,
            'countries': valid_countries
        }
        return render(request, 'fyp/index.html', context)  
    except Exception as e:
        print(f"Unexpected Mediastack Error: {str(e)}")
        context = {
            'success': False,
            'error': f"An unexpected error occurred while fetching Indian news: {str(e)}",
            'current_category': category,
            'current_country': 'in',
            'categories': valid_categories,
            'countries': valid_countries
        }
        return render(request, 'fyp/index.html', context)

def fetch_newsapi_news(request, category, country, valid_categories, valid_countries):
    """Fetch news using NewsAPI for non-Indian countries"""
    
    try:
        api_key = config('NEWS_API_KEY')  
    except Exception as e:
        print(f"Error getting NewsAPI key: {e}")
        context = {
            'success': False,
            'error': "NewsAPI key not configured properly. Please check your .env file.",
            'current_category': category,
            'current_country': country,
            'categories': valid_categories,
            'countries': valid_countries
        }
        return render(request, 'fyp/index.html', context)
  
    # Enhanced URL construction with better debugging
    url = f"https://newsapi.org/v2/top-headlines?category={category}&country={country}&language=en&sortBy=popularity&apiKey={api_key}"
    
    # Debug print
    print(f"=== NEWSAPI DEBUG INFO ===")
    print(f"Requested Country: {country} ({valid_countries.get(country)})")
    print(f"Requested Category: {category}")
    print(f"API URL: {url.replace(api_key, 'HIDDEN_API_KEY')}")

    try:
        response = requests.get(url, timeout=15)  # Increased timeout
        
        # Enhanced debugging
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Check if the request was successful
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_message = f"NewsAPI returned status code {response.status_code}"
            
            if response.status_code == 401:
                error_message += " - Invalid API key"
            elif response.status_code == 429:
                error_message += " - API rate limit exceeded. Try again later."
            elif response.status_code == 426:
                error_message += " - Upgrade required (free tier limitations)"
            elif response.status_code == 400:
                error_message += f" - Bad request: {error_data.get('message', 'Unknown error')}"
            
            print(f"NewsAPI Error Response: {error_data}")
            raise requests.RequestException(error_message)
            
        all_news = response.json()
        
        # Enhanced debugging
        print(f"NewsAPI Response Keys: {list(all_news.keys())}")
        print(f"Total Results: {all_news.get('totalResults', 'N/A')}")
        print(f"Status: {all_news.get('status', 'N/A')}")
        
        if 'articles' in all_news:
            print(f"Number of articles returned: {len(all_news['articles'])}")
            if len(all_news['articles']) == 0:
                print("WARNING: NewsAPI returned 0 articles")
        else:
            print("ERROR: No 'articles' key in response")
            print(f"Full response: {json.dumps(all_news, indent=2)}")
        
        # Check for API errors in response
        if all_news.get('status') == 'error':
            error_msg = all_news.get('message', 'Unknown API error')
            print(f"NewsAPI Error Message: {error_msg}")
            raise requests.RequestException(f"NewsAPI Error: {error_msg}")
        
        # Check if 'articles' exists in response
        if 'articles' not in all_news:
            raise KeyError("No 'articles' found in NewsAPI response")
            
        articles = all_news['articles']
        
        # Handle case where articles list is empty
        if not articles:
            print(f"No articles found for country={country}, category={category}")
            context = {
                'success': True,  # Still success, just no articles
                'articles': [],
                'current_category': category,
                'current_country': country,
                'categories': valid_categories,
                'countries': valid_countries,
                'debug_info': {
                    'total_results': all_news.get('totalResults', 0),
                    'api_status': all_news.get('status', 'unknown'),
                    'country_name': valid_countries.get(country, country),
                    'no_articles_reason': f"No articles available for {valid_countries.get(country, country)} in {category} category",
                    'api_used': 'NewsAPI'
                }
            }
            return render(request, 'fyp/index.html', context)
        
        processed_articles = []
        for i, article in enumerate(articles):
            if article:  # Make sure article is not None
                processed_article = {
                    'title': article.get('title', 'No title available'),
                    'description': article.get('description', 'No description available'),
                    'image': article.get('urlToImage', ''),
                    'url': article.get('url', '#'),  
                    'source': article.get('source', {}).get('name', 'Unknown Source'),
                    'published_at': article.get('publishedAt', '')
                }
                processed_articles.append(processed_article)
                
                # Debug first few articles
                if i < 3:
                    print(f"Article {i+1}: {processed_article['title'][:50]}...")

        print(f"Successfully processed {len(processed_articles)} articles")

        context = {
            'articles': processed_articles,
            'current_category': category,
            'current_country': country,
            'categories': valid_categories,
            'countries': valid_countries,
            'success': True,
            'debug_info': {
                'total_results': all_news.get('totalResults', 0),
                'api_status': all_news.get('status', 'unknown'),
                'country_name': valid_countries.get(country, country),
                'articles_count': len(processed_articles),
                'api_used': 'NewsAPI'
            }
        }
        
        return render(request, 'fyp/index.html', context)
        
    except requests.RequestException as e:
        # Handle API request errors
        print(f"NewsAPI Request Error: {str(e)}")
        context = {
            'success': False,
            'error': f"Failed to fetch news: {str(e)}",
            'current_category': category,
            'current_country': country,
            'categories': valid_categories,
            'countries': valid_countries
        }
        return render(request, 'fyp/index.html', context)  
    except KeyError as e:
        print(f"NewsAPI Data Error: {str(e)}")
        context = {
            'success': False,
            'error': f"Invalid API response: {str(e)}",
            'current_category': category,
            'current_country': country,
            'categories': valid_categories,
            'countries': valid_countries
        }
        return render(request, 'fyp/index.html', context)  
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected NewsAPI Error: {str(e)}")
        context = {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}",
            'current_category': category,
            'current_country': country,
            'categories': valid_categories,
            'countries': valid_countries
        }
        return render(request, 'fyp/index.html', context) 

def landing_page(request):
    """Landing page view with featured news and registration/login buttons"""
    # Get a few latest news for featured section (default to US news)
    try:
        api_key = config('NEWS_API_KEY')
        url = f"https://newsapi.org/v2/top-headlines?country=us&language=en&pageSize=3&apiKey={api_key}"
        
        featured_articles = []
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            news_data = response.json()
            if 'articles' in news_data:
                featured_articles = news_data['articles']
    except Exception as e:
        # If there's any error, just show an empty featured section
        print(f"Error fetching featured articles: {e}")
        featured_articles = []
    
    context = {
        'featured_articles': featured_articles
    }
    return render(request, 'fyp/landing.html', context)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('index')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'fyp/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'fyp/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')