<div align="center">
  <img src="static/images/icon.svg" alt="Digestarr Icon" width="128" height="128">
  <h1>Digestarr</h1>
</div>

**Digestarr** is a Python-based tool that formulates and sends out daily digests about new TV shows and movies sourced from Sonarr and Radarr for your Plex, Jellyfin, or Emby server. Built with a user-friendly web configurator, Digestarr simplifies managing API keys, scheduling updates, and delivering notifications via Telegram and WhatsApp (using [ChatMeBot](https://chatmebot.com)).

---

## Features

- **Daily Media Digest:** Automatically compiles and sends a daily digest of new media content detected by Sonarr and Radarr.
- **Flexible Scheduling:** Set specific days and times for when the daily digest should be sent.
- **Multi-Channel Messaging:** Deliver notifications via Telegram and WhatsApp (powered by [ChatMeBot](https://chatmebot.com)).
- **Web-Based Configurator:** Easily manage your configuration, API keys, and scheduling options through a Flask-powered interface.
- **Future Enhancements:** Planned features include AI-driven personalized summaries, recommendation engines, and expanded household productivity capabilities.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Git (optional)

### Downloading the Code

You have two options to obtain the code:

#### Using Git

Clone the repository with:

```bash
git clone https://github.com/yourusername/Digestarr.git
cd Digestarr
```

#### Download as ZIP

If you prefer not to use Git, you can download the repository as a ZIP file directly from GitHub:
1. Navigate to the [Digestarr GitHub repository](https://github.com/yourusername/Digestarr).
2. Click the green **Code** button.
3. Select **Download ZIP**.
4. Extract the downloaded ZIP file.

### Setting Up the Virtual Environment

1. **Create a Python Virtual Environment:**

    ```bash
    python -m venv venv
    ```

2. **Activate the Virtual Environment:**

    - On macOS/Linux:

      ```bash
      source venv/bin/activate
      ```

    - On Windows:

      ```bash
      venv\Scripts\activate
      ```

3. **Install the Project Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

---

## Usage

### Running the Configurator

Digestarr’s configurator is a Flask-based web interface for setting up your media hosts, API keys, credentials, and scheduling for your daily digest.

1. **Start the Configurator:**

    ```bash
    bin/python config_editor.py
    ```

2. **Access the Interface:**

    Open your browser and navigate to `http://<SERVER_IP>:5000` (replace `<SERVER_IP>` with your server’s IP address).

3. **Configure Your Settings:**

    - **Media Hosts & Recipients:** Enter your Sonarr and Radarr host addresses and specify the number of recipients.
    - **Messaging Platforms:** Enable Telegram and/or WhatsApp. (WhatsApp messages are sent using [ChatMeBot](https://chatmebot.com).)
    - **API Keys:** Enter your API keys for Sonarr, Radarr, Mistral, OMDB, and Telegram.
    - **Scheduling:** 
        - Use the time picker to set the scheduled time (e.g., `09:38`) for your daily digest.
        - Select the days of the week on which the daily digest should be sent.
    - **Screenshot Preview:**

      ![Configurator Screenshot](configurator.png)

4. **Save Configuration:**

    Click the **Save** button to write your settings to the `.env` files. The scheduler will then use these settings to run `main.py` at the specified times to compile and send your daily digest.

### How It Works

- **Scheduling:**  
  Digestarr uses APScheduler (integrated into the configurator script) to read your scheduling settings (`SCHEDULE_TIME` and `SCHEDULE_DAYS`) from the `.env` file. At the configured time(s), it automatically executes `main.py` to fetch media data, compose your daily digest, and send notifications.

- **Messaging:**  
  The daily digest is delivered via Telegram, and WhatsApp messages are dispatched through ChatMeBot.

- **Logging:**  
  Console logs provide insight into scheduler initialization and job execution. Check your terminal output for detailed logs if troubleshooting is needed.

---

## Roadmap

### Current Features

- Web-based configurator for managing API keys, credentials, and scheduling.
- Scheduled execution of `main.py` to send a daily media digest.
- Integration with Sonarr, Radarr, Telegram, and ChatMeBot for WhatsApp messaging.

### Upcoming Improvements

- **Enhanced AI Capabilities:** Personalized summaries and recommendation engines.
- **Expanded Messaging Platforms:** Additional channels for notifications.
- **Improved Logging:** More robust logging and error handling.

### Known Issues

- Occasional timing discrepancies in content updates.
- Further UI enhancements needed for additional configuration fields.

---

## License

Digestarr is released under the [MIT License](LICENSE).

---

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests for improvements or bug fixes.
