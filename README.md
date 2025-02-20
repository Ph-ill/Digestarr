<div align="center">
  <img src="static/images/icon.png" alt="Digestarr Icon" width="128" height="128">
  <h1>Digestarr</h1>
</div>

**Digestarr** (pronounced “di-JEST-arr”) is a Python-based tool that compiles and sends daily media digests about new TV shows and movies sourced from Sonarr and Radarr for your Plex, Jellyfin, or Emby server. With a user-friendly Flask configurator, Digestarr simplifies managing API keys, scheduling updates, and delivering notifications via Telegram and WhatsApp (using [ChatMeBot](https://chatmebot.com)).

---

## Features

- **Daily Media Digest:** Automatically compiles and sends daily digests of new media content.
- **Flexible Scheduling:** Set specific days and times for sending the digest.
- **Multi-Channel Messaging:** Receive notifications via Telegram and WhatsApp.
- **User-Friendly Configurator:** Easily manage configuration, API keys, and scheduling.
- **Future Enhancements:** Planned features include AI-driven personalized summaries, recommendation engines, and expanded messaging options.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Git (optional)

### Downloading the Code

#### Using Git

```bash
git clone https://github.com/yourusername/Digestarr.git
cd Digestarr
```

#### Download as ZIP

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

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

---

## Deployment

To run Digestarr’s configurator continuously in the background on a Debian server, create a systemd service file. For example, create `/etc/systemd/system/digestarr.service` with the following content (adjust paths and user details accordingly):

```ini
[Unit]
Description=Digestarr Configurator Service
After=network.target

[Service]
User=yourusername
Group=yourgroup
WorkingDirectory=/path/to/Digestarr
ExecStart=/path/to/Digestarr/venv/bin/python config_editor.py
Restart=always
Environment=FLASK_APP=config_editor.py
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

To check your user group on Debian, run:

```bash
groups
```

Then, reload systemd and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start digestarr.service
sudo systemctl enable digestarr.service
```

---

## Usage

### Running the Configurator Manually

Digestarr’s configurator is a Flask-based web interface that lets you configure media hosts, API keys, credentials, and scheduling.

1. **Start the Configurator:**

    ```bash
    bin/python config_editor.py
    ```

2. **Access the Interface:**

    Open your browser and navigate to `http://<SERVER_IP>:5000` (replace `<SERVER_IP>` with your server's IP address).

3. **Configure Your Settings:**

   - Enter your Sonarr and Radarr host addresses and specify the number of recipients.
   - Enable Telegram and/or WhatsApp (WhatsApp messages are sent using [ChatMeBot](https://chatmebot.com)).
   - Provide the necessary API keys (Sonarr, Radarr, Mistral, OMDB, Telegram, etc.).
   - Set the scheduled time (e.g., `09:38`) and select the days for the digest.
   - Use the **Send Test Message** button to verify your configuration in real time.
      - When clicked, the button will display a loading indicator until a modal shows the result.

4. **Save Configuration:**

   Click **Save** to update your `.env` files. The scheduler will then use these settings to run `main.py` at the scheduled times.

---

## Screenshots

### Configurator Interface

![Configurator Screenshot](readme_images/configurator.png)

### Telegram Message Example

<div align="center">
  <img src="readme_images/telegram.png" alt="Telegram Message" width="280">
</div>

---

## How It Works

- **Scheduling:** Digestarr uses APScheduler (via the Flask configurator) to read scheduling settings (`SCHEDULE_TIME` and `SCHEDULE_DAYS`) from your `.env` file. At the specified time(s), it executes `main.py` to fetch media data, compose a digest, and send notifications.
- **Messaging:** Notifications are delivered via Telegram and WhatsApp (using ChatMeBot).
- **Logging:** Console logs provide insight into scheduler initialization and job execution for troubleshooting.

---

## Roadmap

### Current Features

- Web-based configurator for managing API keys, credentials, and scheduling.
- Scheduled execution of `main.py` to send daily media digests.
- Integration with Sonarr, Radarr, Telegram, and ChatMeBot for WhatsApp messaging.

### Upcoming Improvements

- Enhanced AI capabilities: Personalized summaries and recommendation engines.
- Expanded messaging platforms.
- More robust logging (console and file).

### Known Issues

- Occasional timing discrepancies in content updates.
- The current build runs on Flask’s development server; switching to a production server is required before the first release.
- Additional UI enhancements for configuration fields.

---

## License

Digestarr is released under the [MIT License](LICENSE).

---

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests for improvements or bug fixes.

*Note: Git is not required to run Digestarr—you can also download the source code as a ZIP from GitHub and follow the installation instructions above.*
