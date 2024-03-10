import json
import os
import time
from dataclasses import asdict
from json import JSONDecodeError

from loguru import logger
from requests import HTTPError

from app.discord_client import DiscordClient
from app.twitch_client import StreamInformation, TwitchClient


class Main:
    is_live: bool = False
    current_stream_id: str = ""
    streams: dict[str, StreamInformation] = dict()

    def __init__(self):
        self.twitch_client = TwitchClient(streamer=os.environ["STREAMER_NAME"])
        self.twitch_client.update_access_token()
        self.profile_image = self.twitch_client.get_streamer_profile_picture()
        self.discord_client = DiscordClient()
        try:
            with open("streams.json", "r") as file:
                saved_streams = json.load(file)
                for stream_id, saved_stream in saved_streams:
                    self.streams[stream_id] = StreamInformation(**saved_stream)
        except (FileNotFoundError, JSONDecodeError):
            pass

    def update_status(self):
        try:
            stream = self.twitch_client.get_stream()

            if not stream:
                if self.is_live:
                    logger.info("Streamer went offline.")
                    self.is_live = False
                    stream = self.streams.get(self.current_stream_id)
                    if stream:
                        self.discord_client.finalize_information_on_discord(
                            streamer_name=stream.user_name,
                            vod_url=self.twitch_client.get_vod(
                                user_id=stream.user_id
                            ),
                        )
                return

            if not self.is_live:
                logger.info("Streamer went live.")
                existing_stream = self.streams.get(stream.id)
                if existing_stream:
                    logger.info(
                        "Recovering from crash, updating discord if possible."
                    )
                    self.is_live = True
                    if existing_stream.discord_message_id:
                        self.discord_client.notification_msg_id = (
                            existing_stream.discord_message_id
                        )
                        self.discord_client.update_information_on_discord(
                            stream=stream, profile_image=self.profile_image
                        )
                    return

                self.is_live = True
                self.current_stream_id = stream.id
                self.streams[stream.id] = stream
                self.discord_client.send_information_to_discord(
                    stream=stream, profile_image=self.profile_image
                )
                self.streams[
                    stream.id
                ].discord_message_id = self.discord_client.notification_msg_id
            else:
                self.discord_client.update_information_on_discord(
                    stream=stream, profile_image=self.profile_image
                )
        except HTTPError as e:
            logger.exception(e)

    def interrupt(self):
        if not self.is_live:
            return

        self.is_live = False
        stream = self.streams.get(self.current_stream_id)
        if stream:
            self.discord_client.finalize_information_on_discord(
                streamer_name=stream.user_name,
                vod_url=self.twitch_client.get_vod(user_id=stream.user_id),
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
            with open("streams.json", "w") as file:
                serializable_streams = {
                    k: asdict(v) for k, v in main.streams.items()
                }
                json.dump(serializable_streams, file)
            time.sleep(
                DELAY_SECONDS - ((time.time() - start_time) % DELAY_SECONDS)
            )
    except (SystemExit, KeyboardInterrupt):
        logger.info("Caught wish to exit, interrupting and re-raising.")
        main.interrupt()
        raise


if __name__ == "__main__":  # pragma: no cover
    entry()
