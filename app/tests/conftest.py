from collections import namedtuple
from unittest import mock

import pytest


@pytest.fixture
def mock_loggers():
    with (
        mock.patch("loguru.logger.info") as info_logger,
        mock.patch("loguru.logger.warning") as warning_logger,
        mock.patch("loguru.logger.error") as error_logger,
    ):
        mocked_loggers = namedtuple(
            "mocked_loggers", ["info_logger", "warning_logger", "error_logger"]
        )
        yield mocked_loggers(info_logger, warning_logger, error_logger)
