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

load_dotenv(dotenv_path='config.env', override=True)
load_dotenv(dotenv_path='credentials.env', override=True)

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

# Weather module settings using lat/lon
weather_enabled = os.getenv('WEATHER_ENABLED', 'false').lower() == 'true'
weather_latitude = os.getenv('WEATHER_LATITUDE', '')
weather_longitude = os.getenv('WEATHER_LONGITUDE', '')

timedeltastore = 0

sonarr_configuration = sonarr.Configuration(host=sonarr_host)
sonarr_configuration.api_key['apikey'] = sonarr_api_key
sonarr_configuration.api_key['X-Api-Key'] = sonarr_api_key

radarr_configuration = radarr.Configuration(host=radarr_host)
radarr_configuration.api_key['apikey'] = radarr_api_key
radarr_configuration.api_key['X-Api-Key'] = radarr_api_key

today = str(date.today() + timedelta(days=timedeltastore))

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
    start = today + 'T00:00:00'
    end = today + 'T23:59:59'
    try:
        radarr_api_response = radarr_api_instance.list_calendar(start=start, end=end)
        parsed_movies = [parse_movie_resource(movie) for movie in radarr_api_response]
    except RadarrApiException as e:
        print(f"Exception when calling CalendarApi->list_calendar: {e}\n")

current_time = datetime.now() + timedelta(days=timedeltastore)

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
    start = today + 'T00:00:00+06:00'
    end = today + 'T23:59:59+06:00'
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

# If weather is enabled and both latitude and longitude are provided, get the forecast.
weather_line = ""
if weather_enabled and weather_latitude and weather_longitude:
    condition, temperature_str = get_weather_forecast_by_coords(weather_latitude, weather_longitude)
    if condition not in ["Weather data unavailable", "Weather data error"]:
        if ai_enabled:
            # Generate a single emoji based solely on the condition text.
            emoji = generate_emojis_from_text(condition, ai_api_key, num_emojis=1)
            condition_line = f"{condition} {emoji}"
        else:
            condition_line = condition
        weather_line = f"=^..^= Today's Weather =^..^=\n{condition_line}\n{temperature_str}\n"
    else:
        weather_line = condition  # This will be "Weather data unavailable" or an error message.


message_body = f"{weather_line}\n=^..^= Today's Content =^..^=\n📺 TV Shows:\n{sonarr_messages}\n\n🎥 Movies:\n{radarr_messages}"

print(message_body)

for i in range(num_recipients):
    if whatsapp_enabled:
        phone_number = os.getenv(f"PHONE_NUMBER_{i+1}")
        api_key = os.getenv(f"PHONE_NUMBER_{i+1}_API_KEY")
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={message_body}&apikey={api_key}"
        response = requests.get(url)
        print(response.text)
    if telegram_enabled:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={os.getenv(f'TELEGRAM_CHAT_ID_{i+1}')}&text={message_body}&disable_web_page_preview=true"
        print(requests.get(url).json())
