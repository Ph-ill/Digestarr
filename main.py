import os
import time
import random
import requests
from datetime import datetime, date, timedelta, timezone
from dotenv import load_dotenv
import sonarr
import radarr
from sonarr.rest import ApiException as SonarrApiException
from radarr.rest import ApiException as RadarrApiException
from functions import generate_emojis_from_text, add_leading_zero_if_single_digit, format_air_time, get_weather_forecast_by_coords
from pprint import pprint
import re
import json

load_dotenv(dotenv_path='config.env', override=True)
load_dotenv(dotenv_path='credentials.env', override=True)

# Retrieve settings and module enable flags
sonarr_host = os.getenv('SONARR_HOST')
radarr_host = os.getenv('RADARR_HOST')
num_recipients = int(os.getenv('NUM_RECIPIENTS'))
whatsapp_enabled = os.getenv('WHATSAPP_ENABLED').lower() == 'true'
telegram_enabled = os.getenv('TELEGRAM_ENABLED').lower() == 'true'
ai_enabled = os.getenv('AI_ENABLED').lower() == 'true'

ai_api_key = os.getenv('MISTRAL_API_KEY')
omdb_api_key = os.getenv('OMDB_API_KEY')
sonarr_api_key = os.getenv('SONARR_API_KEY')
radarr_api_key = os.getenv('RADARR_API_KEY')
telegram_token = os.getenv('TELEGRAM_TOKEN')

# Module enable flags
media_enabled = os.getenv('MEDIA_ENABLED', 'false').lower() == 'true'
custom_enabled = os.getenv('CUSTOM_ENABLED', 'false').lower() == 'true'
weather_module_enabled = os.getenv('WEATHER_ENABLED', 'false').lower() == 'true'
news_enabled = os.getenv('NEWS_ENABLED', 'false').lower() == 'true'
ticker_enabled = os.getenv('TICKER_ENABLED', 'false').lower() == 'true'

# Weather settings
weather_latitude = os.getenv('WEATHER_LATITUDE', '')
weather_longitude = os.getenv('WEATHER_LONGITUDE', '')

# News module settings – three categories and country
news_category_1 = os.getenv('NEWS_CATEGORY_1', 'none')
news_category_2 = os.getenv('NEWS_CATEGORY_2', 'none')
news_category_3 = os.getenv('NEWS_CATEGORY_3', 'none')
news_categories = [news_category_1, news_category_2, news_category_3]
news_country = os.getenv('NEWS_COUNTRY', 'us')

# Ticker module: expect TICKER_ENTRIES as a JSON string (list of objects with keys "type" and "symbol")
try:
    ticker_entries = json.loads(os.getenv('TICKER_ENTRIES', '[]'))
except Exception:
    ticker_entries = []

#Adjust the date for sonarr/radarr calendar module, keep at 0 for current date, -1 for previous day etc. 
day_adjust = 0

sonarr_configuration = sonarr.Configuration(host=sonarr_host)
sonarr_configuration.api_key['apikey'] = sonarr_api_key
sonarr_configuration.api_key['X-Api-Key'] = sonarr_api_key

radarr_configuration = radarr.Configuration(host=radarr_host)
radarr_configuration.api_key['apikey'] = radarr_api_key
radarr_configuration.api_key['X-Api-Key'] = radarr_api_key

def adjust_to_utc(dt):
    """
    Adjust a given datetime object to UTC based on the system's local timezone.
    If the datetime is naive (has no tzinfo), it is assumed to be in local time.
    """
    # If dt is naive, attach the local timezone.
    if dt.tzinfo is None:
        local_tz = datetime.now().astimezone().tzinfo
        dt = dt.replace(tzinfo=local_tz)
    # Convert to UTC.
    return dt.astimezone(timezone.utc)

# Example usage:
local_dt = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)  # local time at 15:30
utc_dt = adjust_to_utc(local_dt)
#print("Local:", local_dt)
#print("UTC:", utc_dt)

def escape_markdown_v2(text):
    escape_chars = r'_*\[\]()~`>#+\-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def fetch_imdb_score(movie_title, is_series=False):
    try:
        url = f"http://www.omdbapi.com/?t={movie_title}&apikey={omdb_api_key}"
        response = requests.get(url)
        data = response.json()
        if data.get('Response') == 'True':
            imdb_rating = data.get('imdbRating', 'N/A')
            imdb_link = f"https://www.imdb.com/title/{data.get('imdbID')}/"
            return imdb_rating, imdb_link
        else:
            return 'N/A', ''
    except Exception as e:
        print(f"Error fetching IMDb rating for {movie_title}: {e}")
        return 'N/A', ''

def parse_movie_resource(resource_obj):
    parsed_data = {
        'title': resource_obj.title,
        'year': resource_obj.year,
        'physical_release': resource_obj.physical_release,
        'digital_release': resource_obj.digital_release,
        'monitored': resource_obj.monitored,
        'status': resource_obj.status,
        'minimum_availability': resource_obj.minimum_availability,
        'air_date_utc': getattr(resource_obj, 'air_date_utc', None)
    }
    return parsed_data

with radarr.ApiClient(radarr_configuration) as radarr_api_client:
    radarr_api_instance = radarr.CalendarApi(radarr_api_client)
 
    current_date = datetime.now()
    start_current_tz = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = adjust_to_utc(start_current_tz)
    end_current_tz = current_date.replace(hour=23,minute=59,second=59,microsecond=999999)
    end_utc = adjust_to_utc(end_current_tz)
    start = str(start_utc + timedelta(days=day_adjust))
    print("radarr")
    print("start: "+start)
    end = str(end_utc + timedelta(days=day_adjust))
    print("end: "+end)

    try:
        radarr_api_response = radarr_api_instance.list_calendar(start=start, end=end)
        parsed_movies = [parse_movie_resource(movie) for movie in radarr_api_response]
    except RadarrApiException as e:
        print(f"Exception when calling CalendarApi->list_calendar: {e}\n")

def parse_episode_resource(resource_obj):
    parsed_data = {
        'series_id': resource_obj.series_id,
        'season_number': resource_obj.season_number,
        'episode_number': resource_obj.episode_number,
        'id': resource_obj.id,
        'title': resource_obj.title,
        'air_date': resource_obj.air_date,
        'air_date_utc': resource_obj.air_date_utc,
        'runtime': resource_obj.runtime,
        'monitored': resource_obj.monitored
    }
    if isinstance(resource_obj.air_date_utc, datetime):
        parsed_data['air_date_utc'] = resource_obj.air_date_utc.replace(tzinfo=None)
    return parsed_data

with sonarr.ApiClient(sonarr_configuration) as api_client:
    api_instance = sonarr.CalendarApi(api_client)

    current_date = datetime.now()
    start_current_tz = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = adjust_to_utc(start_current_tz)
    end_current_tz = current_date.replace(hour=23,minute=59,second=59,microsecond=999999)
    end_utc = adjust_to_utc(end_current_tz)
    start = str(start_utc + timedelta(days=day_adjust))
    end = str(end_utc + timedelta(days=day_adjust))

    unmonitored = False
    include_series = False
    include_episode_file = False
    include_episode_images = False
    tags = ''
    try:
        api_response = api_instance.list_calendar(start=start, end=end, unmonitored=unmonitored,
                                                  include_series=include_series,
                                                  include_episode_file=include_episode_file,
                                                  include_episode_images=include_episode_images, tags=tags)
        parsed_list = [parse_episode_resource(resource) for resource in api_response]
    except SonarrApiException as e:
        print(f"Exception when calling CalendarApi->list_calendar: {e}\n")

def extract_series_name(series_id):
    with sonarr.ApiClient(sonarr_configuration) as api_client:
        api_instance = sonarr.SeriesApi(api_client)
        try:
            api_response = api_instance.get_series_by_id(series_id)
            return api_response.title
        except SonarrApiException as e:
            print(f"Exception when calling SeriesApi->get_series_by_id: {e}\n")
            return None

sonarr_messages = "\n-\n".join([
    f"{extract_series_name(data['series_id'])} - {data['title']}" +
    (f" {generate_emojis_from_text(data['title'], ai_api_key)}" if ai_enabled else "") + "\n"
    f"Airing: {format_air_time(data['air_date_utc'])}\n"
    f"S{add_leading_zero_if_single_digit(str(data['season_number']))}E{add_leading_zero_if_single_digit(str(data['episode_number']))}\n"
    f"Rating: {fetch_imdb_score(extract_series_name(data['series_id']), is_series=True)[0]}/10\n"
    f"{fetch_imdb_score(extract_series_name(data['series_id']), is_series=True)[1]}"
    for data in parsed_list
])
if not sonarr_messages:
    sonarr_messages = "Sorry no shows today 😔"

radarr_messages = "\n-\n".join([
    f"{movie['title']} ({movie['year']}) {generate_emojis_from_text(movie['title'], ai_api_key) if ai_enabled else ''}\n"
    f"Airing: {format_air_time(movie['air_date_utc'])}\n"
    f"Rating: {fetch_imdb_score(movie['title'])[0]}/10\n"
    f"{fetch_imdb_score(movie['title'])[1]}"
    for movie in parsed_movies
])
if not radarr_messages:
    radarr_messages = "Sorry no movies today 😭"

# --- New functions for weather and custom messages ---

def get_weather_text():
    if weather_module_enabled and weather_latitude and weather_longitude:
        condition, temperature_str = get_weather_forecast_by_coords(weather_latitude, weather_longitude)
        if condition not in ["Weather data unavailable", "Weather data error"]:
            if ai_enabled:
                emoji = generate_emojis_from_text(condition, ai_api_key, num_emojis=1)
                condition_line = f"{condition} {emoji}"
            else:
                condition_line = condition
            weather_text_telegram = f"*__Today's Weather__*\n{escape_markdown_v2(condition_line)}\n{escape_markdown_v2(temperature_str)}"
            weather_text_whatsapp = f"_*Today's Weather*_\n{condition_line}\n{temperature_str}"
        else:
            weather_text_telegram = condition
            weather_text_whatsapp = condition
    else:
        weather_text_telegram = ""
        weather_text_whatsapp = ""
    return weather_text_telegram, weather_text_whatsapp

def get_custom_text():
    today_abbr = datetime.now().strftime("%a").lower()
    custom_message = ""
    if today_abbr == "mon":
        custom_message = os.getenv("MON_MESSAGE", "")
    elif today_abbr == "tue":
        custom_message = os.getenv("TUE_MESSAGE", "")
    elif today_abbr == "wed":
        custom_message = os.getenv("WED_MESSAGE", "")
    elif today_abbr == "thu":
        custom_message = os.getenv("THU_MESSAGE", "")
    elif today_abbr == "fri":
        custom_message = os.getenv("FRI_MESSAGE", "")
    elif today_abbr == "sat":
        custom_message = os.getenv("SAT_MESSAGE", "")
    elif today_abbr == "sun":
        custom_message = os.getenv("SUN_MESSAGE", "")
    
    if custom_message:
        custom_text_telegram = f"*__MOTD__*\n{escape_markdown_v2(custom_message)}"
        custom_text_whatsapp = f"_*MOTD*_\n{custom_message}"
    else:
        custom_text_telegram = ""
        custom_text_whatsapp = ""
    return custom_text_telegram, custom_text_whatsapp

# New functions for fetching ticker data
def get_crypto_ticker(ticker):
    # Using CoinGecko’s simple price endpoint
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ticker.lower(),  # user should enter the coin id (e.g. "bitcoin")
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if ticker.lower() in data:
            price = data[ticker.lower()]["usd"]
            change = data[ticker.lower()]["usd_24h_change"]
            return price, change
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching crypto data for {ticker}: {e}")
        return None, None

def get_stock_ticker(ticker):
    # Using Yahoo's unofficial endpoint
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker.upper()}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        result = data.get("quoteResponse", {}).get("result", [])
        if result:
            price = result[0].get("regularMarketPrice", None)
            change = result[0].get("regularMarketChangePercent", None)
            return price, change
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching stock data for {ticker}: {e}")
        return None, None

def format_ticker_line(ticker_type, ticker_symbol):
    # Decide on an emoji for the ticker type:
    type_emoji = "🪙" if ticker_type == "crypto" else "📈"
    # Fetch data accordingly:
    if ticker_type == "crypto":
        price, change = get_crypto_ticker(ticker_symbol)
    else:
        price, change = get_stock_ticker(ticker_symbol)
    if price is None or change is None:
        return f"{type_emoji} - {ticker_symbol.upper()} - Data unavailable"
    # Choose change emoji:
    change_emoji = "🟢" if change >= 0 else "🔴"
    # Format the value (round price and change percent)
    price_formatted = f"{price:.2f}"
    change_formatted = f"{change:.2f}%"
    return f"{type_emoji} - {ticker_symbol.upper()} - ${price_formatted} - {change_emoji} - {change_formatted}"

# Generate news headlines
def get_news_headlines_for_categories(categories):
    news_api_key = os.getenv("NEWS_API_KEY")
    if not news_api_key:
        return "News API key not configured"
    headlines_per_category = []
    for category in categories:
        if category.lower() == "none":
            continue
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": news_api_key,
            "category": category,
            "country": news_country,
            "pageSize": 1
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            if data.get("status") == "ok":
                articles = data.get("articles", [])
                headlines = []
                for article in articles:
                    title = article.get("title", "No Title")
                    description = article.get("description", "")
                    article_url = article.get("url", "")
                    raw_headline = f"{title} - {description}\n{article_url}"
                    escaped_headline = escape_markdown_v2(raw_headline)
                    headlines.append(escaped_headline)
                if headlines:
                    headlines_per_category.append(f"*{category.capitalize()}*\n" + "\n-\n".join(headlines))
            else:
                headlines_per_category.append(f"*{category.capitalize()}* - News data unavailable")
        except Exception as e:
            headlines_per_category.append(f"*{category.capitalize()}* - Error: {e}")
    if headlines_per_category:
        return "\n\n".join(headlines_per_category)
    else:
        return ""

if news_enabled:
    news_headlines = get_news_headlines_for_categories(news_categories)
    news_text_telegram = f"*__News & Headlines__*\n{news_headlines}" if news_headlines else ""
    news_text_whatsapp = f"_*News & Headlines*_\n{news_headlines}" if news_headlines else ""
else:
    news_text_telegram = ""
    news_text_whatsapp = ""

# Generate media text
if sonarr_messages.strip() or radarr_messages.strip():
    media_text_telegram = f"*__Today's Content__*\n📺 *TV Shows:*\n{escape_markdown_v2(sonarr_messages)}\n\n🎥 *Movies:*\n{escape_markdown_v2(radarr_messages)}"
    media_text_whatsapp = f"_*Today's Content*_\n📺 *TV Shows:*\n{sonarr_messages}\n\n🎥 *Movies:*\n{radarr_messages}"
else:
    media_text_telegram = ""
    media_text_whatsapp = ""

# Generate ticker text
ticker_text_telegram = ""
ticker_text_whatsapp = ""
if ticker_enabled and ticker_entries:
    ticker_lines = []
    for entry in ticker_entries:
        # Each entry should be a dict with keys "type" and "symbol"
        ticker_type = entry.get("type", "stock").lower()
        ticker_symbol = entry.get("symbol", "")
        if ticker_symbol:
            ticker_lines.append(format_ticker_line(ticker_type, ticker_symbol))
    if ticker_lines:
        ticker_text_telegram = "*__Ticker Data__*\n" + "\n".join(ticker_lines)
        ticker_text_whatsapp = "_*Ticker Data*_\n" + "\n".join(ticker_lines)

# Compose final message based on enabled modules
custom_text_telegram, custom_text_whatsapp = get_custom_text()
weather_text_telegram, weather_text_whatsapp = get_weather_text()

parts_telegram = []
parts_whatsapp = []

if custom_enabled and custom_text_telegram:
    parts_telegram.append(custom_text_telegram)
    parts_whatsapp.append(custom_text_whatsapp)
if weather_module_enabled and weather_text_telegram:
    parts_telegram.append(weather_text_telegram)
    parts_whatsapp.append(weather_text_whatsapp)
if media_enabled and media_text_telegram:
    parts_telegram.append(media_text_telegram)
    parts_whatsapp.append(media_text_whatsapp)
if news_enabled and news_text_telegram:
    parts_telegram.append(news_text_telegram)
    parts_whatsapp.append(news_text_whatsapp)
if ticker_enabled and ticker_text_telegram:
    parts_telegram.append(ticker_text_telegram)
    parts_whatsapp.append(ticker_text_whatsapp)

if not parts_telegram:
    print("No modules enabled or no content available; no message will be sent.")
    exit(0)

message_body_telegram = "\n\n".join(parts_telegram)
message_body_whatsapp = "\n\n".join(parts_whatsapp)

print("Telegram Message:\n", message_body_telegram)
print("WhatsApp Message:\n", message_body_whatsapp)

for i in range(num_recipients):
    if whatsapp_enabled:
        phone_number = os.getenv(f"PHONE_NUMBER_{i+1}")
        api_key = os.getenv(f"PHONE_NUMBER_{i+1}_API_KEY")
        params = {
            "phone": phone_number,
            "text": message_body_whatsapp,
            "apikey": api_key
        }
        response = requests.get("https://api.callmebot.com/whatsapp.php", params=params)
        print("WhatsApp response:", response.text)
    if telegram_enabled:
        chat_id = os.getenv(f"TELEGRAM_CHAT_ID_{i+1}")
        params = {
            "chat_id": chat_id,
            "text": message_body_telegram,
            "disable_web_page_preview": "true",
            "parse_mode": "MarkdownV2"
        }
        response = requests.get(f"https://api.telegram.org/bot{telegram_token}/sendMessage", params=params)
        print("Telegram response:", response.json())