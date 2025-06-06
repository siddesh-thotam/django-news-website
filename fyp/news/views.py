from django.shortcuts import render, redirect
import requests
from datetime import datetime, timedelta
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decouple import config

@login_required
def index(request):
    
    today = datetime.now()
    from_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')  
    
    
    category = request.GET.get('category', 'general')
    
    valid_categories = ['general', 'business', 'technology', 'health', 'science', 'sports', 'entertainment']
    
    if category not in valid_categories:
        category = 'general'
    
    api_key = config('NEWS_API_KEY')  
  
    url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&sortBy=popularity&apiKey={api_key}"

    try:
        response = requests.get(url)
        # Check if the request was successful
        if response.status_code != 200:
            error_message = f"API returned status code {response.status_code}: {response.text}"
            raise requests.RequestException(error_message)
            
        all_news = response.json()
        
       
        print(f"API Response status: {response.status_code}")
        print(f"API Response contains 'articles': {'articles' in all_news}")
        if 'articles' in all_news:
            print(f"Number of articles: {len(all_news['articles'])}")
        
        # Check if 'articles' exists in response
        if 'articles' not in all_news:
            raise KeyError("No 'articles' found in API response")
            
        articles = all_news['articles']
        
        processed_articles = []
        for article in articles:
            processed_articles.append({
                'title': article.get('title', 'No title available'),
                'description': article.get('description', 'No description available'),
                'image': article.get('urlToImage', ''),
                'url': article.get('url', '#'),  
                'source': article.get('source', {}).get('name', 'Unknown Source'),
                'published_at': article.get('publishedAt', '')
            })

        context = {
            'articles': processed_articles,
            'current_category': category,
            'categories': valid_categories,
            'success': True
        }
        
        return render(request, 'fyp/index.html', context)
        
    except requests.RequestException as e:
        # Handle API request errors
        print(f"API Request Error: {str(e)}")
        context = {
            'success': False,
            'error': f"Failed to fetch news: {str(e)}",
            'current_category': category,
            'categories': valid_categories
        }
        return render(request, 'fyp/index.html', context)  
    except KeyError as e:
        print(f"Data Error: {str(e)}")
        context = {
            'success': False,
            'error': f"Invalid API response: {str(e)}",
            'current_category': category,
            'categories': valid_categories
        }
        return render(request, 'fyp/index.html', context)  
        # Catch any other unexpected errors
        print(f"Unexpected Error: {str(e)}")
        context = {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}",
            'current_category': category,
            'categories': valid_categories
        }
        return render(request, 'fyp/index.html', context) 

def landing_page(request):
    """Landing page view with featured news and registration/login buttons"""
    # Get a few latest news for featured section
    api_key = "16d7900e8ffd437ba7628e3b7f7a521c"
    url = f"https://newsapi.org/v2/top-headlines?category=general&language=en&pageSize=3&apiKey={api_key}"
    
    featured_articles = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news_data = response.json()
            if 'articles' in news_data:
                featured_articles = news_data['articles']
    except:
        # If there's any error, just show an empty featured section
        pass
    
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

    