import os
from mistralai import Mistral
from datetime import timezone
import datetime


# Modified function to ensure leading zeros are only added where applicable
def add_leading_zero_if_single_digit(s):
    if isinstance(s, str) and s.isdigit() and len(s) == 1:
        return '0' + s
    return s

# Function to generate emojis based on text
def generate_emojis_from_text(text, api_key, model="mistral-large-latest"):
    """
    Generate 3 emojis for the given text using Mistral API.

    Args:
        text (str): The input text for which emojis need to be generated.
        api_key (str): Your Mistral API key.
        model (str): The Mistral model to use (default is "mistral-large-latest").

    Returns:
        str: A string of 3 emojis or an error message if something goes wrong.
    """
    try:
        # Initialize the Mistral client
        client = Mistral(api_key=api_key)

        # Request to the API
        chat_response = client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": f"Generate 3 emojis for the following text: {text}, output nothing other than the emojis",
                },
            ]
        )

        # Extract the generated emojis from the response
        emoji_string = chat_response.choices[0].message.content.strip()
        return emoji_string
    except Exception as e:
        return f"Error occurred: {e}"


def format_air_time(air_date_utc):
    """
    Convert a datetime (or ISO string) representing air_date_utc to local time,
    formatted in 12-hour format with AM/PM.
    """
    # If the input is a datetime object:
    if isinstance(air_date_utc, datetime.datetime):
        dt = air_date_utc
    else:
        # Try to parse the ISO format string:
        try:
            dt = datetime.datetime.fromisoformat(air_date_utc)
        except Exception:
            return str(air_date_utc)
    
    # If datetime is naive, assume it's in UTC:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to local timezone:
    local_dt = dt.astimezone()
    return local_dt.strftime('%I:%M %p')