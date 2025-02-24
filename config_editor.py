import os
import sys
import threading
import socket
import logging
from flask import Flask, render_template, request, jsonify, redirect
from dotenv import load_dotenv, set_key
from pathlib import Path
import subprocess
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
app = Flask(__name__)
scheduler = BackgroundScheduler()

config_env_file = Path('config.env')
credentials_env_file = Path('credentials.env')
load_dotenv(dotenv_path=config_env_file)
load_dotenv(dotenv_path=credentials_env_file)
INITIAL_PORT = int(os.environ.get('DIGESTARR_PORT', '5000'))

def get_local_ip():
    try:
        hostname, aliaslist, ipaddrlist = socket.gethostbyname_ex(socket.gethostname())
        for ip in ipaddrlist:
            if ip.startswith("192.168."):
                return ip
        return ipaddrlist[0] if ipaddrlist else "127.0.0.1"
    except Exception:
        return "127.0.0.1"

def save_to_env_file(env_file, data):
    updated_lines = []
    for key, value in data.items():
        if value is None:
            continue
        updated_lines.append(f"{key}={value}\n")
    with open(env_file, 'w') as file:
        file.writelines(updated_lines)

def run_main_script():
    logging.info(f"Running main.py at {datetime.datetime.now()}")
    result = subprocess.run(['bin/python', 'main.py'], capture_output=True, text=True)
    logging.info(f"main.py executed. Return code: {result.returncode}")
    logging.debug(f"Output from main.py: {result.stdout}")
    if result.stderr:
        logging.error(f"Errors from main.py: {result.stderr}")

def update_scheduler():
    schedule_time = os.getenv("SCHEDULE_TIME", "08:00")
    schedule_days = os.getenv("SCHEDULE_DAYS", "").strip()
    if not schedule_days:
        logging.info("No schedule days selected; scheduler will not run.")
        try:
            scheduler.remove_job('main_script_job')
            logging.debug("Existing job 'main_script_job' removed.")
        except Exception:
            logging.debug("No existing job to remove.")
        return
    logging.debug(f"Updating scheduler with time: {schedule_time}, days: {schedule_days}")
    try:
        hour, minute = map(int, schedule_time.split(":"))
    except ValueError:
        logging.error("Invalid SCHEDULE_TIME format. Using default 08:00.")
        hour, minute = 8, 0
    try:
        scheduler.remove_job('main_script_job')
        logging.debug("Existing job 'main_script_job' removed.")
    except Exception:
        logging.debug("No existing job to remove.")
    scheduler.add_job(
        run_main_script,
        trigger='cron',
        day_of_week=schedule_days,
        hour=hour,
        minute=minute,
        id='main_script_job',
        replace_existing=True
    )
    logging.info(f"Scheduler updated: main.py will run on {schedule_days} at {schedule_time}.")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save':
            try:
                num_recipients = int(request.form.get('NUM_RECIPIENTS', '1'))
                schedule_time = request.form.get('SCHEDULE_TIME', '08:00')
                schedule_days_list = [d.strip() for d in request.form.getlist('SCHEDULE_DAYS') if d.strip()]
                schedule_days_str = ','.join(schedule_days_list)
                digestarr_ip = request.form.get('DIGESTARR_IP', '127.0.0.1')
                digestarr_port = request.form.get('DIGESTARR_PORT', '5000')
                
                # Media Content settings
                sonarr_host = request.form.get('SONARR_HOST', '')
                radarr_host = request.form.get('RADARR_HOST', '')
                
                # Module Enablement flags
                media_enabled = 'true' if 'MEDIA_ENABLED' in request.form else 'false'
                custom_enabled = 'true' if 'CUSTOM_ENABLED' in request.form else 'false'
                weather_enabled = 'true' if 'WEATHER_ENABLED' in request.form else 'false'
                news_enabled = 'true' if 'NEWS_ENABLED' in request.form else 'false'
                ticker_enabled = 'true' if 'TICKER_ENABLED' in request.form else 'false'
                
                # Weather settings
                weather_latitude = request.form.get('WEATHER_LATITUDE', '')
                weather_longitude = request.form.get('WEATHER_LONGITUDE', '')
                weather_temp_unit = request.form.get('WEATHER_TEMP_UNIT', 'celsius').lower()
                
                # News country and categories
                news_country = request.form.get('NEWS_COUNTRY', 'us')
                news_category_1 = request.form.get('NEWS_CATEGORY_1', 'none')
                news_category_2 = request.form.get('NEWS_CATEGORY_2', 'none')
                news_category_3 = request.form.get('NEWS_CATEGORY_3', 'none')
                
                # Custom Day Messages settings
                custom_days_list = [d.strip() for d in request.form.getlist('CUSTOM_DAYS') if d.strip()]
                custom_days_str = ','.join(custom_days_list)
                mon_message = request.form.get('MON_MESSAGE', '')
                tue_message = request.form.get('TUE_MESSAGE', '')
                wed_message = request.form.get('WED_MESSAGE', '')
                thu_message = request.form.get('THU_MESSAGE', '')
                fri_message = request.form.get('FRI_MESSAGE', '')
                sat_message = request.form.get('SAT_MESSAGE', '')
                sun_message = request.form.get('SUN_MESSAGE', '')
                
                # Ticker module: receive ticker entries as JSON string
                ticker_entries = request.form.get('TICKER_ENTRIES', '[]')
                
                config_values = {
                    'DIGESTARR_IP': digestarr_ip,
                    'DIGESTARR_PORT': digestarr_port,
                    'SONARR_HOST': sonarr_host,
                    'RADARR_HOST': radarr_host,
                    'NUM_RECIPIENTS': str(num_recipients),
                    'WHATSAPP_ENABLED': 'true' if 'WHATSAPP_ENABLED' in request.form else 'false',
                    'TELEGRAM_ENABLED': 'true' if 'TELEGRAM_ENABLED' in request.form else 'false',
                    'AI_ENABLED': 'true' if 'AI_ENABLED' in request.form else 'false',
                    'SCHEDULE_TIME': schedule_time,
                    'SCHEDULE_DAYS': schedule_days_str,
                    'WEATHER_LATITUDE': weather_latitude,
                    'WEATHER_LONGITUDE': weather_longitude,
                    'WEATHER_TEMP_UNIT': weather_temp_unit,
                    'NEWS_ENABLED': news_enabled,
                    'NEWS_COUNTRY': news_country,
                    'NEWS_CATEGORY_1': news_category_1,
                    'NEWS_CATEGORY_2': news_category_2,
                    'NEWS_CATEGORY_3': news_category_3,
                    'CUSTOM_DAYS': custom_days_str,
                    'MON_MESSAGE': mon_message,
                    'TUE_MESSAGE': tue_message,
                    'WED_MESSAGE': wed_message,
                    'THU_MESSAGE': thu_message,
                    'FRI_MESSAGE': fri_message,
                    'SAT_MESSAGE': sat_message,
                    'SUN_MESSAGE': sun_message,
                    'CUSTOM_ENABLED': custom_enabled,
                    'MEDIA_ENABLED': media_enabled,
                    'WEATHER_ENABLED': weather_enabled,
                    'TICKER_ENABLED': ticker_enabled,
                    'TICKER_ENTRIES': ticker_entries
                }
                
                save_to_env_file(config_env_file, config_values)
                credentials_values = {
                    'SONARR_API_KEY': request.form['SONARR_API_KEY'],
                    'RADARR_API_KEY': request.form['RADARR_API_KEY'],
                    'MISTRAL_API_KEY': request.form['MISTRAL_API_KEY'],
                    'OMDB_API_KEY': request.form['OMDB_API_KEY'],
                    'TELEGRAM_TOKEN': request.form['TELEGRAM_TOKEN'],
                    'NEWS_API_KEY': request.form.get('NEWS_API_KEY', '')
                }
                for i in range(1, num_recipients + 1):
                    if request.form.get(f'PHONE_NUMBER_{i}', ''):
                        credentials_values[f'PHONE_NUMBER_{i}'] = request.form.get(f'PHONE_NUMBER_{i}', '')
                    if request.form.get(f'PHONE_NUMBER_{i}_API_KEY', ''):
                        credentials_values[f'PHONE_NUMBER_{i}_API_KEY'] = request.form.get(f'PHONE_NUMBER_{i}_API_KEY', '')
                    if request.form.get(f'TELEGRAM_CHAT_ID_{i}', ''):
                        credentials_values[f'TELEGRAM_CHAT_ID_{i}'] = request.form.get(f'TELEGRAM_CHAT_ID_{i}', '')
                save_to_env_file(credentials_env_file, credentials_values)
                load_dotenv(dotenv_path=config_env_file, override=True)
                load_dotenv(dotenv_path=credentials_env_file, override=True)
                logging.debug("Configuration saved and .env files reloaded.")
                update_scheduler()
                new_port = int(digestarr_port)
                if new_port != INITIAL_PORT:
                    logging.info(f"Port changed from {INITIAL_PORT} to {new_port}. Restarting server...")
                    def restart_server():
                        import time
                        time.sleep(2)
                        os.environ['DIGESTARR_PORT'] = str(new_port)
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                    threading.Thread(target=restart_server).start()
                    new_url = f"http://{digestarr_ip}:{new_port}"
                    return f"""
                    <html>
                      <head>
                        <title>Server Restarting</title>
                      </head>
                      <body style="font-family: Helvetica, sans-serif; text-align: center; padding: 20px;">
                        <h2>Configuration Saved</h2>
                        <p>The Digestarr port has been changed to <strong>{new_port}</strong> and the IP is set to <strong>{digestarr_ip}</strong>.</p>
                        <p>Please navigate to <a href="{new_url}">{new_url}</a> to access the configurator.</p>
                      </body>
                    </html>
                    """
                else:
                    return redirect('/')
            except Exception as e:
                logging.error(f"Exception in save branch: {e}")
                return f"Error: {e}", 500
        elif action == 'run_script':
            try:
                result = subprocess.run(['bin/python', 'main.py'], capture_output=True, text=True)
                status = 'success' if result.returncode == 0 else 'error'
                message = 'Test message sent successfully!' if result.returncode == 0 else 'Script execution failed!'
                logging.debug(f"Manual run_script action executed. Output: {result.stdout}")
            except Exception as e:
                status = 'error'
                message = str(e)
                logging.error(f"Error running main.py: {e}")
            return jsonify({'status': status, 'message': message})
    load_dotenv(dotenv_path=config_env_file, override=True)
    load_dotenv(dotenv_path=credentials_env_file, override=True)
    config_data = {
        'DIGESTARR_IP': os.getenv('DIGESTARR_IP', '127.0.0.1').strip(),
        'DIGESTARR_PORT': os.getenv('DIGESTARR_PORT', '5000'),
        'SONARR_HOST': os.getenv('SONARR_HOST', ''),
        'RADARR_HOST': os.getenv('RADARR_HOST', ''),
        'NUM_RECIPIENTS': os.getenv('NUM_RECIPIENTS', '1'),
        'WHATSAPP_ENABLED': os.getenv('WHATSAPP_ENABLED', 'false'),
        'TELEGRAM_ENABLED': os.getenv('TELEGRAM_ENABLED', 'false'),
        'AI_ENABLED': os.getenv('AI_ENABLED', 'false'),
        'SCHEDULE_TIME': os.getenv('SCHEDULE_TIME', '08:00'),
        'SCHEDULE_DAYS': os.getenv('SCHEDULE_DAYS', '').strip(),
        'WEATHER_LATITUDE': os.getenv('WEATHER_LATITUDE', ''),
        'WEATHER_LONGITUDE': os.getenv('WEATHER_LONGITUDE', ''),
        'WEATHER_TEMP_UNIT': os.getenv('WEATHER_TEMP_UNIT', 'celsius').lower(),
        'CUSTOM_DAYS': os.getenv('CUSTOM_DAYS', '').strip(),
        'MON_MESSAGE': os.getenv('MON_MESSAGE', ''),
        'TUE_MESSAGE': os.getenv('TUE_MESSAGE', ''),
        'WED_MESSAGE': os.getenv('WED_MESSAGE', ''),
        'THU_MESSAGE': os.getenv('THU_MESSAGE', ''),
        'FRI_MESSAGE': os.getenv('FRI_MESSAGE', ''),
        'SAT_MESSAGE': os.getenv('SAT_MESSAGE', ''),
        'SUN_MESSAGE': os.getenv('SUN_MESSAGE', ''),
        'MEDIA_ENABLED': os.getenv('MEDIA_ENABLED', 'false'),
        'CUSTOM_ENABLED': os.getenv('CUSTOM_ENABLED', 'false'),
        'WEATHER_ENABLED': os.getenv('WEATHER_ENABLED', 'false'),
        'NEWS_ENABLED': os.getenv('NEWS_ENABLED', 'false'),
        'NEWS_CATEGORY_1': os.getenv('NEWS_CATEGORY_1', 'none'),
        'NEWS_CATEGORY_2': os.getenv('NEWS_CATEGORY_2', 'none'),
        'NEWS_CATEGORY_3': os.getenv('NEWS_CATEGORY_3', 'none'),
        'NEWS_COUNTRY': os.getenv('NEWS_COUNTRY', 'us'),
        'TICKER_ENABLED': os.getenv('TICKER_ENABLED', 'false'),
        'TICKER_ENTRIES': os.getenv('TICKER_ENTRIES', '[]')
    }
    credentials_data = {
        'SONARR_API_KEY': os.getenv('SONARR_API_KEY', ''),
        'RADARR_API_KEY': os.getenv('RADARR_API_KEY', ''),
        'MISTRAL_API_KEY': os.getenv('MISTRAL_API_KEY', ''),
        'OMDB_API_KEY': os.getenv('OMDB_API_KEY', ''),
        'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN', ''),
        'NEWS_API_KEY': os.getenv('NEWS_API_KEY', '')
    }
    num_recipients = int(config_data['NUM_RECIPIENTS']) if config_data['NUM_RECIPIENTS'] else 1
    for i in range(1, num_recipients + 1):
        credentials_data[f'PHONE_NUMBER_{i}'] = os.getenv(f'PHONE_NUMBER_{i}', '')
        credentials_data[f'PHONE_NUMBER_{i}_API_KEY'] = os.getenv(f'PHONE_NUMBER_{i}_API_KEY', '')
        key = f'TELEGRAM_CHAT_ID_{i}'
        if i == 1 and not os.getenv(key):
            credentials_data[key] = os.getenv('TELEGRAM_CHAT_ID', '')
        else:
            credentials_data[key] = os.getenv(key, '')
    return render_template('index.html', config_data=config_data, credentials_data=credentials_data, num_recipients=num_recipients)

def init_scheduler():
    schedule_time = os.getenv("SCHEDULE_TIME", "08:00")
    schedule_days = os.getenv("SCHEDULE_DAYS", "").strip()
    if not schedule_days:
        logging.info("No schedule days selected in init_scheduler; scheduler will not run.")
        return
    logging.debug(f"Initializing scheduler with time: {schedule_time}, days: {schedule_days}")
    try:
        hour, minute = map(int, schedule_time.split(":"))
    except ValueError:
        logging.error("Invalid SCHEDULE_TIME format. Using default 08:00.")
        hour, minute = 8, 0
    scheduler.add_job(
        run_main_script,
        trigger='cron',
        day_of_week=schedule_days,
        hour=hour,
        minute=minute,
        id='main_script_job',
        replace_existing=True
    )
    scheduler.start()
    logging.info(f"Scheduler started: main.py will run on {schedule_days} at {schedule_time}.")

if __name__ == '__main__':
    port = int(os.getenv('DIGESTARR_PORT', '5000'))
    logging.info(f"Server running at http://{os.getenv('LOCAL_IP', '127.0.0.1')}:{port}")
    init_scheduler()
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)