import os
import random
from dataclasses import dataclass

import requests
from loguru import logger
from requests import HTTPError
from urllib3.exceptions import NewConnectionError


@dataclass
class CachePrevent:
    calls: int = 0
    random_number: int = 0
    five_minute_update_modulo: int = 10

    def prevent_cache_on_url(self, url: str) -> str:
        self.calls += 1
        if self.calls % self.five_minute_update_modulo == 0:
            self.random_number = random.randint(0, 999999)
            logger.info("Forcing image cache refresh.")

        return f"{url}?{self.random_number}"


@dataclass
class StreamInformation:
    id: str
    user_id: str
    user_name: str
    user_login: str
    title: str
    game_name: str
    viewer_count: int
    started_at: str
    _thumbnail_url: str
    discord_message_id: str = ""

    @property
    def thumbnail_url(self):
        return self._thumbnail_url.replace("{width}", "1280").replace(
            "{height}", "720"
        )


class TwitchClient:
    _access_token: str = ""

    def __init__(self, streamer: str):
        self.streamer = streamer
        self._client_id = os.environ["TWITCH_CLIENT_ID"]
        self._client_secret = os.environ["TWITCH_CLIENT_SECRET"]
        self._cache_prevent = CachePrevent()

    def update_access_token(self) -> None:
        logger.info("Updating twitch access token...")
        response = requests.post(
            url="https://id.twitch.tv/oauth2/token",
            headers={"Content-Type": "application/x-www-form-url-encoded"},
            params={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()

        self._access_token = response.json()["access_token"]
        logger.info("Updating twitch access token done.")

    def _update_access_token_wrapper(self) -> bool:
        try:
            self.update_access_token()
        except HTTPError as e:
            logger.error("API call to update twitch access token failed.")
            logger.exception(e)
            return False
        except KeyError:
            logger.error("Access token was not in auth response.")
            return False
        return True

    def get_streamer_profile_picture(
        self, is_retry: bool = False
    ) -> str | None:
        response = requests.get(
            url="https://api.twitch.tv/helix/users",
            headers={
                "Client-Id": self._client_id,
                "Authorization": f"Bearer {self._access_token}",
            },
            params={"login": self.streamer},
        )

        if response.status_code == 401:
            logger.info("Getting streamer returned an auth issue.")

            if is_retry:
                logger.error("Auth failed twice, aborting.")
                return None

            if not self._update_access_token_wrapper():
                return None

            return self.get_streamer_profile_picture(is_retry=True)

        response.raise_for_status()

        return response.json()["data"][0]["profile_image_url"]

    def get_stream(self, is_retry: bool = False) -> StreamInformation | None:
        try:
            response = requests.get(
                url="https://api.twitch.tv/helix/streams",
                headers={
                    "Client-Id": self._client_id,
                    "Authorization": f"Bearer {self._access_token}",
                },
                params={"user_login": self.streamer},
            )
        except requests.exceptions.ConnectionError:
            logger.warning("Getting streams failed with a connection Error.")
            return None

        if response.status_code == 401:
            logger.info("Getting streams returned an auth issue.")

            if is_retry:
                logger.error("Auth failed twice, aborting.")
                return None

            if not self._update_access_token_wrapper():
                return None

            return self.get_stream(is_retry=True)

        response.raise_for_status()

        streams = response.json()["data"]
        if len(streams) == 0:
            return None

        stream_data = streams[0]
        return StreamInformation(
            id=stream_data.get("id"),
            user_id=stream_data.get("user_id"),
            user_name=stream_data.get("user_name"),
            user_login=stream_data.get("user_login"),
            title=stream_data.get("title"),
            game_name=stream_data.get("game_name"),
            viewer_count=stream_data.get("viewer_count"),
            started_at=stream_data.get("started_at"),
            _thumbnail_url=self._cache_prevent.prevent_cache_on_url(
                url=stream_data.get("thumbnail_url"),
            ),
        )

    def get_vod(self, user_id: str, is_retry: bool = False) -> str | None:
        try:
            response = requests.get(
                url="https://api.twitch.tv/helix/videos",
                headers={
                    "Client-Id": self._client_id,
                    "Authorization": f"Bearer {self._access_token}",
                },
                params={"user_id": user_id},
            )
        except NewConnectionError as err:
            logger.opt(exception=err).warning(
                "Getting vods failed with a new connection Error, more details below."
            )
            return None

        if response.status_code == 401:
            logger.info("Getting vod returned an auth issue.")

            if is_retry:
                logger.error("Auth failed twice, aborting.")
                return None

            if not self._update_access_token_wrapper():
                return None

            return self.get_vod(user_id=user_id, is_retry=True)

        response.raise_for_status()

        vods = response.json()["data"]
        if len(vods) == 0:
            return None

        vod_data = vods[0]
        return vod_data.get("url")
