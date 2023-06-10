import os
import time

from loguru import logger
from requests import HTTPError

from app.discord_client import DiscordClient
from app.twitch_client import StreamInformation, TwitchClient


class Main:
    is_live: bool = False
    _previous_stream: StreamInformation = None

    def __init__(self):
        self.twitch_client = TwitchClient(streamer=os.environ["STREAMER_NAME"])
        self.twitch_client.update_access_token()
        self.profile_image = self.twitch_client.get_streamer_profile_picture()
        self.discord_client = DiscordClient()

    def update_status(self):
        try:
            stream = self.twitch_client.get_stream()

            if not stream:
                if self.is_live:
                    logger.info("Streamer went offline.")
                    self.is_live = False
                    self.discord_client.finalize_information_on_discord(
                        streamer_name=self._previous_stream.user_name,
                        vod_url=self.twitch_client.get_vod(
                            user_id=self._previous_stream.user_id
                        ),
                    )
                return

            if not self.is_live:
                logger.info("Streamer went live.")
                self.discord_client.send_information_to_discord(
                    stream=stream, profile_image=self.profile_image
                )
                self.is_live = True
            else:
                logger.info("Streamer still live.")
                self.discord_client.update_information_on_discord(
                    stream=stream, profile_image=self.profile_image
                )

            self._previous_stream = stream
        except HTTPError as e:
            logger.exception(e)

    def interrupt(self):
        if not self.is_live:
            return

        self.is_live = False
        self.discord_client.finalize_information_on_discord(
            streamer_name=self._previous_stream.user_login,
            vod_url=self.twitch_client.get_vod(
                user_id=self._previous_stream.user_id
            ),
        )


DELAY_SECONDS = 30.0


def entry() -> None:
    logger.info("Initiating main...")
    start_time = time.time()
    main = Main()

    logger.info("Set-up looks correct, starting main loop.")
    try:
        while True:
            main.update_status()
            time.sleep(
                DELAY_SECONDS - ((time.time() - start_time) % DELAY_SECONDS)
            )
    except (SystemExit, KeyboardInterrupt):
        logger.info("Caught wish to exit, interrupting and re-raising.")
        main.interrupt()
        raise


if __name__ == "__main__":  # pragma: no cover
    entry()
