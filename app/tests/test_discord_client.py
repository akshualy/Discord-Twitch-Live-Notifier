import json
import os
from typing import Any
from unittest import mock

import pytest
import requests_mock
from requests import HTTPError

from app.discord_client import DiscordClient
from app.twitch_client import StreamInformation


def test_require_webhook_url():
    with pytest.raises(KeyError):
        DiscordClient()


def test_send_information_to_discord(mock_loggers):
    stream = StreamInformation(
        user_id="0",
        user_name="Test",
        user_login="test",
        game_name="game",
        started_at="never",
        title="title",
        viewer_count=0,
        _thumbnail_url="https://thumbnail.com/{width}-{height}.png",
    )

    with (
        mock.patch.dict(
            os.environ, {"DISCORD_WEBHOOK_URL": "https://test/url"}
        ),
        requests_mock.Mocker() as requests_mocker,
    ):
        requests_mocker.post(url="https://test/url", json={"id": "0"})

        discord_client = DiscordClient()
        discord_client.send_information_to_discord(
            stream=stream, profile_image="profile_image.png"
        )

    webhook_call = requests_mocker.request_history[0]
    assert webhook_call.url == "https://test/url?wait=true"
    embed: dict[str, Any] = json.loads(webhook_call.text)["embeds"][0]
    assert embed["title"] == "title"
    assert embed["timestamp"] == "never"
    assert embed["url"] == f"https://www.twitch.tv/test"
    assert embed["author"]["name"] == "Test"
    assert embed["author"]["url"] == embed["url"]
    assert embed["author"]["icon_url"] == "profile_image.png"
    assert embed["image"]["url"] == "https://thumbnail.com/1280-720.png"
    assert embed["fields"][0]["value"] == "game"
    assert embed["fields"][1]["value"] == 0


def test_send_information_to_discord_fails(mock_loggers):
    stream = StreamInformation(
        user_id="",
        user_name="",
        user_login="",
        game_name="",
        started_at="",
        title="",
        viewer_count=0,
        _thumbnail_url="",
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
