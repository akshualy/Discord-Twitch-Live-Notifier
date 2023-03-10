import os
import threading
from unittest import mock

import pytest
import requests_mock

from app.main import Main, entry


def test_create_main(mock_loggers):
    with (
        mock.patch.dict(
            os.environ,
            {
                "STREAMER_NAME": "streamer_name",
                "DISCORD_WEBHOOK_URL": "URL",
                "TWITCH_CLIENT_ID": "id",
                "TWITCH_CLIENT_SECRET": "secret",
            },
        ),
        requests_mock.Mocker() as requests_mocker,
    ):
        # We authorize
        requests_mocker.post(
            "https://id.twitch.tv/oauth2/token", json={"access_token": "token"}
        )
        # We cache the profile image URL of the streamer
        requests_mocker.get(
            "https://api.twitch.tv/helix/users?login=streamer_name",
            json={"data": [{"profile_image_url": "image"}]},
        )

        main = Main()

    assert main.discord_client
    assert main.twitch_client
    assert main.profile_image == "image"


def test_run_main_one_iteration(mock_loggers):
    with (
        mock.patch.dict(
            os.environ,
            {
                "STREAMER_NAME": "streamer_name",
                "DISCORD_WEBHOOK_URL": "URL",
                "TWITCH_CLIENT_ID": "id",
                "TWITCH_CLIENT_SECRET": "secret",
            },
        ),
        mock.patch(
            "app.main.Main.update_status",
            side_effect=Main.update_status,
            autospec=True,
        ) as mock_update_status,
        mock.patch("app.main.DELAY_SECONDS", 2),
        requests_mock.Mocker() as requests_mocker,
    ):
        requests_mocker.post(
            "https://id.twitch.tv/oauth2/token", json={"access_token": "token"}
        )
        requests_mocker.get(
            "https://api.twitch.tv/helix/users?login=streamer_name",
            json={"data": [{"profile_image_url": "image"}]},
        )
        requests_mocker.get(
            "https://api.twitch.tv/helix/streams?user_login=streamer_name",
            json={"data": []},
        )

        def delayed_raise():
            mock_update_status.side_effect = KeyboardInterrupt()

        thread = threading.Timer(1, delayed_raise)
        thread.start()

        with pytest.raises(KeyboardInterrupt):
            entry()
