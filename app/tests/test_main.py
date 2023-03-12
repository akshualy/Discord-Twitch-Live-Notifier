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

        # Loop runs normally without streamer going live
        with pytest.raises(KeyboardInterrupt):
            entry()


def test_run_main_streamer_already_live(mock_loggers):
    with (
        mock.patch.dict(
            os.environ,
            {
                "STREAMER_NAME": "streamer_name",
                "DISCORD_WEBHOOK_URL": "https://discord.com/webhook",
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
            json={
                "data": [
                    {
                        "id": "123456789",
                        "user_id": "98765",
                        "user_login": "streamer_name",
                        "user_name": "Streamer_Name",
                        "game_id": "494131",
                        "game_name": "Little Nightmares",
                        "type": "live",
                        "title": "hablamos y le damos a Little Nightmares 1",
                        "tags": ["Español"],
                        "viewer_count": 78365,
                        "started_at": "2021-03-10T15:04:21Z",
                        "language": "es",
                        "thumbnail_url": (
                            "https://static-cdn.jtvnw.net/previews-ttv/"
                            "live_user_auronplay-{width}x{height}.jpg"
                        ),
                        "tag_ids": [],
                        "is_mature": False,
                    }
                ]
            },
        )
        requests_mocker.post(
            "https://discord.com/webhook?wait=true", json={"id": "123456"}
        )
        requests_mocker.patch("https://discord.com/webhook/messages/123456")
        requests_mocker.get(
            "https://api.twitch.tv/helix/videos?user_id=98765",
            json={"data": []},
        )

        def delayed_raise():
            mock_update_status.side_effect = KeyboardInterrupt()

        thread = threading.Timer(4, delayed_raise)
        thread.start()

        # Loop runs normally if streamer is already live
        with pytest.raises(KeyboardInterrupt):
            entry()

    auth_request = requests_mocker.request_history[0]
    assert auth_request.scheme == "https"
    assert auth_request.netloc == "id.twitch.tv"
    assert auth_request.path == "/oauth2/token"
    assert auth_request.query == (
        "client_id=id&client_secret=secret&grant_type=client_credentials"
    )

    get_user_request = requests_mocker.request_history[1]
    assert get_user_request.scheme == "https"
    assert get_user_request.netloc == "api.twitch.tv"
    assert get_user_request.path == "/helix/users"
    assert get_user_request.query == "login=streamer_name"

    get_streams_request = requests_mocker.request_history[2]
    assert get_streams_request.scheme == "https"
    assert get_streams_request.netloc == "api.twitch.tv"
    assert get_streams_request.path == "/helix/streams"
    assert get_streams_request.query == "user_login=streamer_name"

    create_notification_request = requests_mocker.request_history[3]
    assert create_notification_request.query == "wait=true"
    # Exact JSON field population tested in test_discord_client.py
    assert create_notification_request.json()

    second_loop_get_streams_request = requests_mocker.request_history[4]
    assert second_loop_get_streams_request.scheme == "https"
    assert second_loop_get_streams_request.netloc == "api.twitch.tv"
    assert second_loop_get_streams_request.path == "/helix/streams"
    assert second_loop_get_streams_request.query == "user_login=streamer_name"

    update_notification_request = requests_mocker.request_history[5]
    assert update_notification_request.path == "/webhook/messages/123456"
    assert update_notification_request.json()

    get_vod_request = requests_mocker.request_history[-2]
    assert get_vod_request.scheme == "https"
    assert get_vod_request.netloc == "api.twitch.tv"
    assert get_vod_request.path == "/helix/videos"
    assert get_vod_request.query == "user_id=98765"

    finalize_notification_request = requests_mocker.request_history[-1]
    assert finalize_notification_request.path == "/webhook/messages/123456"
    assert finalize_notification_request.json()
