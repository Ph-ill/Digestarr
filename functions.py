import os
from mistralai import Mistral

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
