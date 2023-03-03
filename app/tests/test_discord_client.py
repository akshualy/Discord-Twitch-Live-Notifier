import os
from unittest import mock

import pytest
import requests_mock
from requests import HTTPError

from app.discord_client import DiscordClient
from app.twitch_client import StreamInformation


def test_require_webhook_url():
    with pytest.raises(KeyError):
        DiscordClient()


def test_send_information_to_discord_fails(mock_loggers):
    stream = StreamInformation(
        user_id="",
        user_name="",
        user_login="",
        game_name="",
        started_at="",
        title="",
        viewer_count=0,
        _thumbnail_url=""
    )

    with (
        mock.patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "https://test"}),
        requests_mock.Mocker() as requests_mocker,
    ):
        requests_mocker.post(url="https://test", status_code=400)

        discord_client = DiscordClient()
        with pytest.raises(HTTPError):
            discord_client.send_information_to_discord(
                stream=stream, profile_image=""
            )

    assert len(mock_loggers.info_logger.call_args_list) == 1
    assert mock_loggers.info_logger.call_args.args[0] == (
        "Sending a message with an embed to the webhook..."
    )
