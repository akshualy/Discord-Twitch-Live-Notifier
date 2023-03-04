import os

import requests
from loguru import logger

from app.twitch_client import StreamInformation


class DiscordClient:
    _notification_msg_id: str = ""

    def __init__(self):
        self._webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

    def send_information_to_discord(
        self, stream: StreamInformation, profile_image: str
    ) -> None:
        logger.info("Sending a message with an embed to the webhook...")
        streamer_url = f"https://www.twitch.tv/{stream.user_login}"
        response = requests.post(
            url=f"{self._webhook_url}?wait=true",
            json={
                "username": "Oak Tree",
                "avatar_url": "https://i.imgur.com/DBOuwjx.png",
                "content": f"@everyone {stream.user_name} went live!",
                "embeds": [
                    {
                        "title": stream.title,
                        "color": 8388863,
                        "timestamp": stream.started_at,
                        "url": streamer_url,
                        "author": {
                            "name": stream.user_name,
                            "url": streamer_url,
                            "icon_url": profile_image,
                        },
                        "image": {"url": stream.thumbnail_url},
                        "fields": [
                            {
                                "name": "Game",
                                "value": stream.game_name,
                                "inline": True,
                            },
                            {
                                "name": "Viewers",
                                "value": stream.viewer_count,
                                "inline": True,
                            },
                        ],
                    }
                ],
            },
        )

        response.raise_for_status()

        self._notification_msg_id = response.json()["id"]
        logger.info("Stream information sent with ping to Discord.")

    def update_information_on_discord(
        self, stream: StreamInformation, profile_image: str
    ) -> None:
        logger.info("Updating stream information on Discord...")
        streamer_url = f"https://www.twitch.tv/{stream.user_login}"
        response = requests.patch(
            url=f"{self._webhook_url}/messages/{self._notification_msg_id}",
            json={
                "embeds": [
                    {
                        "title": stream.title,
                        "color": 8388863,
                        "timestamp": stream.started_at,
                        "url": streamer_url,
                        "author": {
                            "name": f"{stream.user_name}",
                            "url": streamer_url,
                            "icon_url": profile_image,
                        },
                        "image": {"url": stream.thumbnail_url},
                        "fields": [
                            {
                                "name": "Game",
                                "value": stream.game_name,
                                "inline": True,
                            },
                            {
                                "name": "Viewers",
                                "value": stream.viewer_count,
                                "inline": True,
                            },
                        ],
                    }
                ],
            },
        )
        response.raise_for_status()
        logger.info("Message embed content updated.")

    def finalize_information_on_discord(
        self, streamer_name, vod_url: str | None
    ) -> None:
        logger.info("Finalizing stream information on Discord...")
        if not self._notification_msg_id:
            logger.info("Message ID not set, nothing to finalize.")
            return

        if not vod_url:
            vod_url = "None available. Please contact the developer."

        response = requests.patch(
            url=f"{self._webhook_url}/messages/{self._notification_msg_id}",
            json={
                "username": "Oak Tree",
                "avatar_url": "https://i.imgur.com/DBOuwjx.png",
                "content": (
                    f"{streamer_name} stopped the stream. Check out the VOD!"
                    f"\n{vod_url}"
                ),
                "embeds": [],
            },
        )
        response.raise_for_status()
        logger.info("Message updated with VOD.")
