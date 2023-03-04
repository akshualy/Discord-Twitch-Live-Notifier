import os
from unittest import mock

import requests_mock

from app.main import Main


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
