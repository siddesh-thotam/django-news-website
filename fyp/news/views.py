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
    
    try:
        api_key = config('NEWS_API_KEY')  
    except Exception as e:
        print(f"Error getting API key: {e}")
        context = {
            'success': False,
            'error': "API key not configured properly. Please check your .env file.",
            'current_category': category,
            'current_country': country,
            'categories': valid_categories,
            'countries': valid_countries
        }
        return render(request, 'fyp/index.html', context)
  
    # Enhanced URL construction with better debugging
    url = f"https://newsapi.org/v2/top-headlines?category={category}&country={country}&language=en&sortBy=popularity&apiKey={api_key}"
    
    # Debug print
    print(f"=== DEBUG INFO ===")
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
            error_message = f"API returned status code {response.status_code}"
            
            if response.status_code == 401:
                error_message += " - Invalid API key"
            elif response.status_code == 429:
                error_message += " - API rate limit exceeded. Try again later."
            elif response.status_code == 426:
                error_message += " - Upgrade required (free tier limitations)"
            elif response.status_code == 400:
                error_message += f" - Bad request: {error_data.get('message', 'Unknown error')}"
            
            print(f"API Error Response: {error_data}")
            raise requests.RequestException(error_message)
            
        all_news = response.json()
        
        # Enhanced debugging
        print(f"API Response Keys: {list(all_news.keys())}")
        print(f"Total Results: {all_news.get('totalResults', 'N/A')}")
        print(f"Status: {all_news.get('status', 'N/A')}")
        
        if 'articles' in all_news:
            print(f"Number of articles returned: {len(all_news['articles'])}")
            if len(all_news['articles']) == 0:
                print("WARNING: API returned 0 articles")
        else:
            print("ERROR: No 'articles' key in response")
            print(f"Full response: {json.dumps(all_news, indent=2)}")
        
        # Check for API errors in response
        if all_news.get('status') == 'error':
            error_msg = all_news.get('message', 'Unknown API error')
            print(f"API Error Message: {error_msg}")
            raise requests.RequestException(f"API Error: {error_msg}")
        
        # Check if 'articles' exists in response
        if 'articles' not in all_news:
            raise KeyError("No 'articles' found in API response")
            
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
                    'no_articles_reason': f"No articles available for {valid_countries.get(country, country)} in {category} category"
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
                'articles_count': len(processed_articles)
            }
        }
        
        return render(request, 'fyp/index.html', context)
        
    except requests.RequestException as e:
        # Handle API request errors
        print(f"API Request Error: {str(e)}")
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
        print(f"Data Error: {str(e)}")
        context = {
            'success': False,
            'error': f"Invalid API response: {str(e)}",
            'current_category': category,
            'current_country': country,
            'categories': valid_countries,
            'categories': valid_categories
        }
        return render(request, 'fyp/index.html', context)  
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected Error: {str(e)}")
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