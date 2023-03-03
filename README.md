# Discord Twitch Live Notification

This is a python project to send a Discord webhook with a self-updating webhook 
when a specified streamer goes live on Twitch.  
Checks and updates exactly once every half minute.

The motivation behind this project is that requiring discord.js or the twitch api library is too much in my opinion.
Doing this requires 7 API calls, including the really basic authentication in twitch's case. 

All options to run this require environment variables. You can see them in [this file](.env).

## Running locally

The first option to run the project is to run it locally.
You may install the dependencies through pip, however it is recommended to install them with the project default, [poetry](https://python-poetry.org).

### Install prerequisites

- Python 3.11.2

Clone the repository:
```commandline
git clone https://github.com/Gadsee/Discord-Twitch-Live-Notifications.git
```

Install poetry. (Taken from the [official documentation](https://python-poetry.org/docs/).)

Debian-based linux distributions:
```bash
sudo apt-get install python3-pip curl
curl -sSL https://install.python-poetry.org | python3 -
```

Windows:
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Install dependencies

```commandline
poetry env use 3.11.2
poetry install
```

### Run the app

Replace `source .env` with your OS' appropriate way of loading environment variables.

```bash
poetry shell
source .env
python app/main.py
```

## Running in Docker

The second option is to run the project's docker image. 

You have two paths you can take here as well:
1. You may fork the project and use the configured pipelines and container registry.
2. You may build the image yourself using the Dockerfile.
