# Messegarr

Python Script to send daily updates about monitored content on radarr and sonarr

<br>
<br>
<br>


## Installation

To install this project first clone the repository and then install the dependencies using 'requirements.txt' 
```
git clone https://github.com/Ph-ill/Messegarr.git
cd messegarr
pip install -r requirements.txt
```
Then edit the files config.env and credentials.env with your api keys and information.


## Usage
To run the project
```
python messegarr/main.py
```
<br>
<br>
<br>

# Task List

## Functions

#### Configurator

- [ ] Test message from configurator
- [ ] Schedule from configurator
- [ ] Run configurator as background service
- [X] Add 'AI Features' checkbox
  - [X] Have mistral api key input field display based on status of checkbox
- [ ] Stop flask logging API Keys in cleartext
- [X]  Dynamically hide whatsapp and telegram credential fields based on enabled functionality


#### General

- [ ] Change name in
  - [ ] Github README.md
  - [ ] Code
  - [ ] Telegram Bot
- [ ] Logging to console & file

## Bugs

- [ ] Some content showing a day late
- [X] imdb links broken
- [X] Emojis before movie year, should be after
- [X] Year not pulling for movie 'The Gorge'
