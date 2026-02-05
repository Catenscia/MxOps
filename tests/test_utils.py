from dataclasses import dataclass, field
import logging
from unittest.mock import MagicMock, patch

import pytest
from mxops.utils.msc import get_account_link, get_tx_link
from mxops.utils.progress import ProgressLogger
from tests.utils import instantiate_assert_all_args_provided


def test_transaction_link():
    # Given
    tx_hash = "3519ff7dd9ed71fb140e2b79a51cfeb9e90df749504bb436ebb697a30f8afcf5"

    # When
    link = get_tx_link(tx_hash)

    # Then
    assert (
        link
        == "http://localhost:3002/transactions/3519ff7dd9ed71fb140e2b79a51cfeb9e90df749504bb436ebb697a30f8afcf5"  # noqa
    )


def test_account_link():
    # Given
    bech32 = "erd1jkd354c4mz9cfp8vjh2cvv2vtc7fg4klfktrqp8c627r6x86sa8qquzu45"

    # When
    link = get_account_link(bech32)

    # Then
    assert (
        link
        == "http://localhost:3002/accounts/erd1jkd354c4mz9cfp8vjh2cvv2vtc7fg4klfktrqp8c627r6x86sa8qquzu45"  # noqa
    )


def test_missing_parameters():
    # Given
    @dataclass
    class MyClass:
        a: 1
        b: int = 7
        c: int = field(init=False)

    # When
    _ = instantiate_assert_all_args_provided(MyClass, {"a": 1, "b": 5})
    with pytest.raises(ValueError, match="Missing parameters: {'b'} for class MyClass"):
        instantiate_assert_all_args_provided(
            MyClass,
            {
                "a": 1,
            },
        )
    with pytest.raises(ValueError, match="Missing parameters: {'a'} for class MyClass"):
        instantiate_assert_all_args_provided(
            MyClass,
            {
                "b": 1,
            },
        )


class TestProgressLogger:
    """Tests for the ProgressLogger class."""

    def test_no_logging_before_threshold(self):
        """Should not log before the time threshold is exceeded."""
        mock_logger = MagicMock(spec=logging.Logger)
        progress = ProgressLogger(
            mock_logger, "Test operation", time_threshold=5.0, log_interval=10.0
        )

        with patch("mxops.utils.progress.time.time") as mock_time:
            # Start at time 0
            mock_time.return_value = 0.0
            progress.start()

            # Update at 2 seconds (before threshold)
            mock_time.return_value = 2.0
            progress.update(100)

            # Update at 4 seconds (still before threshold)
            mock_time.return_value = 4.0
            progress.update(200)

        # No logging should have occurred
        mock_logger.info.assert_not_called()

    def test_logging_after_threshold(self):
        """Should log when the time threshold is exceeded."""
        mock_logger = MagicMock(spec=logging.Logger)
        progress = ProgressLogger(
            mock_logger, "Test operation", time_threshold=5.0, log_interval=10.0
        )

        with patch("mxops.utils.progress.time.time") as mock_time:
            mock_time.return_value = 0.0
            progress.start()

            # Update at 6 seconds (after threshold)
            mock_time.return_value = 6.0
            progress.update(500)

        # Should have logged once
        assert mock_logger.info.call_count == 1
        call_args = mock_logger.info.call_args[0][0]
        assert "Test operation" in call_args
        assert "500" in call_args

    def test_logging_at_intervals(self):
        """Should log at regular intervals after threshold is exceeded."""
        mock_logger = MagicMock(spec=logging.Logger)
        progress = ProgressLogger(
            mock_logger, "Test operation", time_threshold=5.0, log_interval=10.0
        )

        with patch("mxops.utils.progress.time.time") as mock_time:
            mock_time.return_value = 0.0
            progress.start()

            # First log at threshold
            mock_time.return_value = 5.0
            progress.update(100)

            # No log at 10s (only 5s since last log)
            mock_time.return_value = 10.0
            progress.update(200)

            # Log at 15s (10s since last log)
            mock_time.return_value = 15.0
            progress.update(300)

            # No log at 20s (only 5s since last log)
            mock_time.return_value = 20.0
            progress.update(400)

            # Log at 25s (10s since last log)
            mock_time.return_value = 25.0
            progress.update(500)

        # Should have logged 3 times (at 5s, 15s, 25s)
        assert mock_logger.info.call_count == 3

    def test_finish_logs_only_if_threshold_exceeded(self):
        """finish() should only log if the operation was slow."""
        mock_logger = MagicMock(spec=logging.Logger)

        # Fast operation - finish should not log
        progress_fast = ProgressLogger(
            mock_logger, "Fast operation", time_threshold=5.0
        )
        with patch("mxops.utils.progress.time.time") as mock_time:
            mock_time.return_value = 0.0
            progress_fast.start()
            mock_time.return_value = 2.0
            progress_fast.finish(100)

        mock_logger.info.assert_not_called()

        # Slow operation - finish should log
        progress_slow = ProgressLogger(
            mock_logger, "Slow operation", time_threshold=5.0
        )
        with patch("mxops.utils.progress.time.time") as mock_time:
            mock_time.return_value = 0.0
            progress_slow.start()
            mock_time.return_value = 6.0
            progress_slow.update(50)  # Triggers threshold
            mock_time.return_value = 10.0
            progress_slow.finish(100)

        # Two logs: one at update (threshold exceeded), one at finish
        assert mock_logger.info.call_count == 2
        finish_call = mock_logger.info.call_args[0][0]
        assert "completed" in finish_call

    def test_no_logging_without_start(self):
        """Should not log if start() was never called."""
        mock_logger = MagicMock(spec=logging.Logger)
        progress = ProgressLogger(mock_logger, "Test operation")

        progress.update(100)
        progress.finish(100)

        mock_logger.info.assert_not_called()

    def test_extra_info_included_in_log(self):
        """Extra info should be included in log messages."""
        mock_logger = MagicMock(spec=logging.Logger)
        progress = ProgressLogger(
            mock_logger, "Test operation", time_threshold=0.0
        )

        with patch("mxops.utils.progress.time.time") as mock_time:
            mock_time.return_value = 0.0
            progress.start()
            mock_time.return_value = 1.0
            progress.update(100, extra_info="(processing batch 5)")

        call_args = mock_logger.info.call_args[0][0]
        assert "(processing batch 5)" in call_args
