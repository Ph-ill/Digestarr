import os
from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv, set_key
from pathlib import Path

app = Flask(__name__)

# Load .env files
config_env_file = Path('config.env')
credentials_env_file = Path('credentials.env')
load_dotenv(dotenv_path=config_env_file)
load_dotenv(dotenv_path=credentials_env_file)

def save_to_env_file(env_file, data):
    """ Save updated data to the specified .env file, excluding keys with empty values. """
    updated_lines = []

    # Only add variables with non-empty values
    for key, value in data.items():
        if value:
            updated_lines.append(f"{key}={value}\n")

    # Write back the updated content, effectively removing any old variables not in `data`
    with open(env_file, 'w') as file:
        file.writelines(updated_lines)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the number of recipients
        num_recipients = request.form['NUM_RECIPIENTS']
        num_recipients = int(num_recipients) if num_recipients else 1

        # Save the config.env values
        config_values = {
            'SONARR_HOST': request.form['SONARR_HOST'],
            'RADARR_HOST': request.form['RADARR_HOST'],
            'NUM_RECIPIENTS': str(num_recipients),
            'WHATSAPP_ENABLED': 'true' if 'WHATSAPP_ENABLED' in request.form else 'false',
            'TELEGRAM_ENABLED': 'true' if 'TELEGRAM_ENABLED' in request.form else 'false',
            'AI_ENABLED': 'true' if 'AI_ENABLED' in request.form else 'false'
        }
        save_to_env_file(config_env_file, config_values)

        # Save the credentials.env values
        credentials_values = {
            'SONARR_API_KEY': request.form['SONARR_API_KEY'],
            'RADARR_API_KEY': request.form['RADARR_API_KEY'],
            'MISTRAL_API_KEY': request.form['MISTRAL_API_KEY'],
            'OMDB_API_KEY': request.form['OMDB_API_KEY'],
            'TELEGRAM_TOKEN': request.form['TELEGRAM_TOKEN']
        }

        # Add phone numbers and chat IDs dynamically
        for i in range(1, num_recipients + 1):
            phone_number = request.form.get(f'PHONE_NUMBER_{i}', '')
            phone_number_api_key = request.form.get(f'PHONE_NUMBER_{i}_API_KEY', '')
            telegram_chat_id = request.form.get(f'TELEGRAM_CHAT_ID_{i}', '')

            if phone_number:
                credentials_values[f'PHONE_NUMBER_{i}'] = phone_number
            if phone_number_api_key:
                credentials_values[f'PHONE_NUMBER_{i}_API_KEY'] = phone_number_api_key
            if telegram_chat_id:
                credentials_values[f'TELEGRAM_CHAT_ID_{i}'] = telegram_chat_id

        # Save credentials to the .env file
        save_to_env_file(credentials_env_file, credentials_values)

        # Reload the .env files after saving
        load_dotenv(dotenv_path=config_env_file, override=True)
        load_dotenv(dotenv_path=credentials_env_file, override=True)

        return redirect('/')

    # Load existing values for the form
    load_dotenv(dotenv_path=config_env_file)
    load_dotenv(dotenv_path=credentials_env_file)

    # Prepare data for the frontend
    config_data = {
        'SONARR_HOST': os.getenv('SONARR_HOST', ''),
        'RADARR_HOST': os.getenv('RADARR_HOST', ''),
        'NUM_RECIPIENTS': os.getenv('NUM_RECIPIENTS', '1'),
        'WHATSAPP_ENABLED': os.getenv('WHATSAPP_ENABLED', 'false'),
        'TELEGRAM_ENABLED': os.getenv('TELEGRAM_ENABLED', 'false'),
        'AI_ENABLED': os.getenv('AI_ENABLED', 'false')
    }

    credentials_data = {
        'SONARR_API_KEY': os.getenv('SONARR_API_KEY', ''),
        'RADARR_API_KEY': os.getenv('RADARR_API_KEY', ''),
        'MISTRAL_API_KEY': os.getenv('MISTRAL_API_KEY', ''),
        'OMDB_API_KEY': os.getenv('OMDB_API_KEY', ''),
        'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN', '')
    }

    # Generate fields for the phone numbers and chat IDs dynamically
    num_recipients = int(config_data['NUM_RECIPIENTS']) if config_data['NUM_RECIPIENTS'] else 1
    for i in range(1, num_recipients + 1):
        credentials_data[f'PHONE_NUMBER_{i}'] = os.getenv(f'PHONE_NUMBER_{i}', '')
        credentials_data[f'PHONE_NUMBER_{i}_API_KEY'] = os.getenv(f'PHONE_NUMBER_{i}_API_KEY', '')
        credentials_data[f'TELEGRAM_CHAT_ID_{i}'] = os.getenv(f'TELEGRAM_CHAT_ID_{i}', '')

    return render_template('index.html', config_data=config_data, credentials_data=credentials_data, num_recipients=num_recipients)

if __name__ == '__main__':
    port = 5000
    print(f"Server running at http://{os.getenv('LOCAL_IP', '127.0.0.1')}:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)