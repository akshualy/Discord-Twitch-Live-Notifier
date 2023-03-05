# Discord Twitch Live Notification

[![pipeline status](https://gitlab.com/Deko.dev/discord-twitch-live-notifier/badges/main/pipeline.svg)](https://gitlab.com/Deko.dev/discord-twitch-live-notifier/-/commits/main) 
[![coverage report](https://gitlab.com/Deko.dev/discord-twitch-live-notifier/badges/main/coverage.svg)](https://gitlab.com/Deko.dev/discord-twitch-live-notifier/-/commits/main)

This is a python project to send a Discord webhook with a self-updating webhook 
when a specified streamer goes live on Twitch.  
Checks and updates exactly once every half minute.

The motivation behind this project is that requiring discord.js or the twitch api library is too much in my opinion.
The same goes for having to invite a bot just for this purpose.  
The project does 7 API calls, including the really basic authentication in twitch's case.

**Table of contents**
1. [Environment variables (Configuration)](#environment-variables-configuration)
2. [Running in docker](#running-in-docker)
   1. [Using the pre-built docker image from the registry](#using-the-pre-built-docker-image-from-the-registry)
   2. [Building the image yourself](#building-the-image-yourself)
3. [Running locally](#running-locally)
   1. [Install prerequisites](#install-prerequisites)
   2. [Install dependencies](#install-dependencies)
   3. [Run the app](#run-the-app)

## Environment variables (Configuration)

All options to run this require environment variables. You can see them in [this file](.env.example).

**STREAMER_NAME**

This is the easiest one. It holds the all lowercase username of the streamer you wish to notify for.

Examples: `kaicenat`, `xqc`, `esl_csgo`, `steve_the_streamer`, etc.

**DISCORD_WEBHOOK_URL**

Your Discord webhook URL. Acquiring one requires the `Manage Webhooks` permission on Discord.

1. Hover a channel in the server you wish to notify in.
2. Click `Edit Channel` (the cog icon on the right).
3. Go to `Integrations`.
4. Click `Create Webhook` or `Edit Webhooks`, depending on if the channel already has webhooks.
5. Click `New Webhook` (Skip if using an existing one).
6. Click the webhook in the overview, it will expand.
   1. You can give it a name, but the app by default sets it itself.
7. Click `Copy Webhook URL`.

Now you have your webhook URL in your clipboard and can paste it into your .env file.

**TWITCH_CLIENT_ID** and **TWITCH_CLIENT_SECRET**

The bread and butter variables of this application. These are needed to query the Twitch API.  
Please refer to [the official documentation](https://dev.twitch.tv/docs/authentication/register-app/) on how to register an app.
As part of the documentation steps you will generate a client ID and client secret.
Use those in the .env file.

## Running in Docker

The first option - and the option I use - is to run the project's docker image.  
It has the benefit of being able to run multiple instances at the same time.  
*Note: There is a limit by Twitch for how many access tokens you can have active at the same time for the same twitch client.*

You have two paths you can take here:
1. You may use this project's docker image in the container registry.
   1. You may also fork the project and host it in your own registry.
2. You may build the image yourself using the Dockerfile.

You can read up on how to install docker on the [official website](https://docs.docker.com/get-docker/).

### Using the pre-built docker image from the registry

The pipeline builds your image into your gitlab project's docker registry at  
`registry.gitlab.com/<YOUR USERNAME>/discord-twitch-live-notifier:main`.

In my case that's `registry.gitlab.com/dekorated/discord-twitch-live-notifier:main`.

You can use that to pull your image:
```bash
docker image pull registry.gitlab.com/dekorated/discord-twitch-live-notifier:main
```

**Note**: If you use a private repository,you will have to `docker login registry.gitlab.com`
with your username and a gitlab access token as password first.

Then run the image. Take note to adjust the path at `--env-file`.
```bash
docker run \
    --name discord-twitch-live-notifier \
    --env-file /path/to/your/env-file/.env \
    -d \
    registry.gitlab.com/dekorated/discord-twitch-live-notifier:main
```
Your OS may treat line breaks in commands differently, please adjust accordingly. 
The above is tested on linux/debian.

To stop and remove the container (app), run
```bash
docker stop discord-twitch-live-notifier
docker rm discord-twitch-live-notifier 
```

### Building the image yourself

You may also build the image yourself locally:
```commandline
docker build -f Dockerfile -t some_image_tag --build-arg .
```

And then run the image with the same instructions as above.

## Running locally

The second option to run the project is to run it locally.
You may install the dependencies through pip, however it is recommended to install them with the project default, [poetry](https://python-poetry.org).

### Install prerequisites

- Python 3.11.2

Clone the repository:
```commandline
git clone https://github.com/Gadsee/Discord-Twitch-Live-Notifications.git
```

Install poetry (taken from the [official documentation](https://python-poetry.org/docs/)):

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
python -m app.main
```
