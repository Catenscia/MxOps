"""
author: Etienne Wallet

This module contains utilities for progress logging of slow operations.
"""

import logging
import time


class ProgressLogger:
    """
    A utility class that logs progress only for slow operations.

    The logger activates after a time threshold is exceeded, then logs
    progress updates at regular intervals. This avoids log spam for
    fast operations while providing visibility for slow ones.

    Usage:
        progress = ProgressLogger(logger, "Fetching storage keys")
        progress.start()
        for batch in batches:
            # ... process batch ...
            progress.update(total_processed)
        progress.finish()
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation_name: str,
        time_threshold: float = 5.0,
        log_interval: float = 10.0,
    ):
        """
        Initialize the progress logger.

        :param logger: The logger instance to use for output
        :param operation_name: A descriptive name for the operation being tracked
        :param time_threshold: Seconds before logging activates (default 5.0)
        :param log_interval: Seconds between progress updates (default 10.0)
        """
        self.logger = logger
        self.operation_name = operation_name
        self.time_threshold = time_threshold
        self.log_interval = log_interval

        self._start_time: float | None = None
        self._last_log_time: float = 0.0
        self._threshold_exceeded = False
        self._last_count = 0

    def start(self):
        """Start tracking the operation."""
        self._start_time = time.time()
        self._last_log_time = self._start_time
        self._threshold_exceeded = False
        self._last_count = 0

    def update(self, current_count: int, extra_info: str = ""):
        """
        Update progress and log if appropriate.

        Logs are emitted only after the time threshold has been exceeded,
        and then only at the configured interval.

        :param current_count: The current count of items processed
        :param extra_info: Optional additional information to include in the log
        """
        if self._start_time is None:
            return

        self._last_count = current_count  # Always track the count
        now = time.time()
        elapsed = now - self._start_time

        # Check if we've exceeded the threshold
        if not self._threshold_exceeded:
            if elapsed >= self.time_threshold:
                self._threshold_exceeded = True
                self._log_progress(current_count, elapsed, extra_info)
                self._last_log_time = now
            return

        # Log at intervals once threshold is exceeded
        if now - self._last_log_time >= self.log_interval:
            self._log_progress(current_count, elapsed, extra_info)
            self._last_log_time = now

    def _log_progress(self, count: int, elapsed: float, extra_info: str = ""):
        """Log a progress message with rate information."""
        rate = count / elapsed if elapsed > 0 else 0
        extra = f" {extra_info}" if extra_info else ""
        self.logger.info(
            f"{self.operation_name}: "
            f"{count:,} items fetched in {elapsed:.1f}s ({rate:.0f}/s){extra}"
        )

    def finish(self, final_count: int | None = None):
        """
        Log completion summary if the operation was slow.

        :param final_count: The final count of items processed. If None, uses
                          the last count from update().
        """
        if self._start_time is None:
            return

        elapsed = time.time() - self._start_time
        count = final_count if final_count is not None else self._last_count

        # Only log completion if we crossed the threshold
        if self._threshold_exceeded:
            rate = count / elapsed if elapsed > 0 else 0
            self.logger.info(
                f"{self.operation_name} completed: "
                f"{count:,} items in {elapsed:.1f}s ({rate:.0f}/s)"
            )
