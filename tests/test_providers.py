"""Tests for the providers module, specifically the dynamic batch sizing."""

from unittest.mock import MagicMock, patch

import pytest
from multiversx_sdk import AccountStorage, AccountStorageEntry, Address
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout

from mxops.common.providers import (
    _is_retryable_error,
    get_account_storage_with_fallback,
)


class TestIsRetryableError:
    """Tests for the _is_retryable_error helper function."""

    def test_timeout_is_retryable(self):
        error = Timeout("Connection timed out")
        assert _is_retryable_error(error) is True

    def test_connection_error_is_retryable(self):
        error = RequestsConnectionError("Connection refused")
        assert _is_retryable_error(error) is True

    def test_http_error_502_is_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 502
        error = HTTPError(response=mock_response)
        assert _is_retryable_error(error) is True

    def test_http_error_503_is_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 503
        error = HTTPError(response=mock_response)
        assert _is_retryable_error(error) is True

    def test_http_error_504_is_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 504
        error = HTTPError(response=mock_response)
        assert _is_retryable_error(error) is True

    def test_http_error_404_not_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = HTTPError(response=mock_response)
        assert _is_retryable_error(error) is False

    def test_http_error_no_response_not_retryable(self):
        error = HTTPError()
        error.response = None
        assert _is_retryable_error(error) is False

    def test_generic_value_error_not_retryable(self):
        error = ValueError("Invalid argument")
        assert _is_retryable_error(error) is False

    def test_generic_exception_not_retryable(self):
        error = Exception("Some random error")
        assert _is_retryable_error(error) is False


class TestGetAccountStorageWithFallbackBatchReduction:
    """Tests for dynamic batch size reduction in get_account_storage_with_fallback."""

    @pytest.fixture
    def mock_proxy(self):
        """Create a mock proxy network provider."""
        return MagicMock()

    @pytest.fixture
    def test_address(self):
        """Create a test address."""
        return Address.new_from_bech32(
            "erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"
        )

    @pytest.fixture
    def mock_config(self):
        """Mock the Config.get_config() to return test values."""
        with patch("mxops.common.providers.Config") as mock:
            config_instance = MagicMock()
            config_instance.get.side_effect = lambda key: {
                "STORAGE_ITERATION_BATCH_SIZE": "1000",
                "API_RATE_LIMIT": "100",
            }.get(key)
            mock.get_config.return_value = config_instance
            yield mock

    def test_success_without_batch_reduction(
        self, mock_proxy, test_address, mock_config
    ):
        """Test successful iteration without any errors."""
        # Setup: proxy returns data successfully
        mock_response = MagicMock()
        mock_response.to_dictionary.return_value = {
            "pairs": {"6b6579": "76616c7565"},  # "key": "value" in hex
            "newIteratorState": [],  # Empty means iteration complete
        }
        mock_proxy.do_post_generic.return_value = mock_response

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=100, request_delay=0
        )

        assert isinstance(result, AccountStorage)
        assert len(result.entries) == 1
        # Verify batch size was used correctly
        call_args = mock_proxy.do_post_generic.call_args[0][1]
        assert call_args["numKeys"] == 100

    def test_batch_reduction_on_timeout(self, mock_proxy, test_address, mock_config):
        """Test that batch size is reduced when timeout occurs."""
        # First call fails with timeout, second succeeds with smaller batch
        mock_response_success = MagicMock()
        mock_response_success.to_dictionary.return_value = {
            "pairs": {"6b6579": "76616c7565"},
            "newIteratorState": [],
        }

        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call with batch size 200 - timeout
                assert data["numKeys"] == 200
                raise Timeout("Connection timed out")
            else:
                # Second call with batch size 100 - success
                assert data["numKeys"] == 100
                return mock_response_success

        mock_proxy.do_post_generic.side_effect = side_effect

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        assert isinstance(result, AccountStorage)
        assert call_count == 2

    def test_multiple_batch_reductions(self, mock_proxy, test_address, mock_config):
        """Test multiple batch size reductions before success."""
        mock_response_success = MagicMock()
        mock_response_success.to_dictionary.return_value = {
            "pairs": {"6b6579": "76616c7565"},
            "newIteratorState": [],
        }

        call_count = 0
        batch_sizes_used = []

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            batch_sizes_used.append(data["numKeys"])
            if call_count < 3:
                raise Timeout("Connection timed out")
            return mock_response_success

        mock_proxy.do_post_generic.side_effect = side_effect

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=400, request_delay=0, min_batch_size=50
        )

        assert isinstance(result, AccountStorage)
        # 400 -> 200 -> 100 (success)
        assert batch_sizes_used == [400, 200, 100]

    def test_fallback_to_standard_endpoint_when_min_batch_exceeded(
        self, mock_proxy, test_address, mock_config
    ):
        """Test fallback to standard endpoint when min batch size is exceeded."""
        # All iterate-keys calls fail
        mock_proxy.do_post_generic.side_effect = Timeout("Always timeout")

        # Standard endpoint returns storage
        mock_standard_storage = AccountStorage(
            raw={"pairs": {"6b6579": "76616c7565"}},
            entries=[
                AccountStorageEntry(
                    raw={"6b6579": "76616c7565"}, key="key", value=b"value"
                )
            ],
        )
        mock_proxy.get_account_storage.return_value = mock_standard_storage

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=100, request_delay=0, min_batch_size=50
        )

        # Should have called standard endpoint after exhausting batch sizes
        mock_proxy.get_account_storage.assert_called_once_with(test_address)
        assert result == mock_standard_storage

    def test_non_retryable_error_raises(self, mock_proxy, test_address, mock_config):
        """Test that non-retryable errors fall back to standard endpoint."""
        mock_proxy.do_post_generic.side_effect = ValueError("Invalid data")

        mock_standard_storage = AccountStorage(
            raw={"pairs": {}},
            entries=[],
        )
        mock_proxy.get_account_storage.return_value = mock_standard_storage

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=100, request_delay=0
        )

        mock_proxy.get_account_storage.assert_called_once()
        assert result == mock_standard_storage

    def test_iteration_preserves_state_after_batch_reduction(
        self, mock_proxy, test_address, mock_config
    ):
        """Test that iterator state is preserved after batch size reduction."""
        call_count = 0
        iterator_states = []

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            iterator_states.append(data["iteratorState"])

            if call_count == 1:
                # First call succeeds with partial data
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"6b657931": "76616c756531"},
                    "newIteratorState": [[1, 2, 3]],
                }
                return mock_resp
            elif call_count == 2:
                # Second call with new state times out
                raise Timeout("Timeout")
            else:
                # Third call with reduced batch but same state succeeds
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"6b657932": "76616c756532"},
                    "newIteratorState": [],
                }
                return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        assert isinstance(result, AccountStorage)
        # Check that iterator state was preserved after timeout
        assert iterator_states[0] == []  # Initial state
        assert iterator_states[1] == [[1, 2, 3]]  # State from first response
        assert iterator_states[2] == [[1, 2, 3]]  # Same state after retry
        assert len(result.entries) == 2

    def test_connection_error_triggers_batch_reduction(
        self, mock_proxy, test_address, mock_config
    ):
        """Test that ConnectionError triggers batch size reduction."""
        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RequestsConnectionError("Connection refused")
            mock_resp = MagicMock()
            mock_resp.to_dictionary.return_value = {
                "pairs": {"6b6579": "76616c7565"},
                "newIteratorState": [],
            }
            return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        assert isinstance(result, AccountStorage)
        assert call_count == 2

    def test_http_502_triggers_batch_reduction(
        self, mock_proxy, test_address, mock_config
    ):
        """Test that HTTP 502 errors trigger batch size reduction."""
        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_response = MagicMock()
                mock_response.status_code = 502
                raise HTTPError(response=mock_response)
            mock_resp = MagicMock()
            mock_resp.to_dictionary.return_value = {
                "pairs": {"6b6579": "76616c7565"},
                "newIteratorState": [],
            }
            return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        assert isinstance(result, AccountStorage)
        assert call_count == 2

    def test_logging_on_batch_reduction(self, mock_proxy, test_address, mock_config):
        """Test that batch reduction is logged."""
        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Timeout("Connection timed out")
            mock_resp = MagicMock()
            mock_resp.to_dictionary.return_value = {
                "pairs": {"6b6579": "76616c7565"},
                "newIteratorState": [],
            }
            return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        with patch("mxops.common.providers.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            get_account_storage_with_fallback(
                mock_proxy, test_address,
                num_keys=200, request_delay=0, min_batch_size=50
            )

            # Verify logger.info was called with batch reduction message
            mock_logger.info.assert_called()
            log_message = mock_logger.info.call_args[0][0]
            assert "failed with batch size 200" in log_message
            assert "reducing to 100" in log_message

    def test_empty_storage_triggers_fallback(
        self, mock_proxy, test_address, mock_config
    ):
        """Test that empty storage on first request triggers fallback.

        This is intentional behavior: we can't distinguish between "endpoint not
        enabled" and "empty storage" from the API response, so we fall back to
        the standard endpoint which will return empty storage if that's the case.
        """
        mock_response = MagicMock()
        mock_response.to_dictionary.return_value = {
            "pairs": {},
            "newIteratorState": [],
        }
        mock_proxy.do_post_generic.return_value = mock_response

        mock_standard_storage = AccountStorage(raw={"pairs": {}}, entries=[])
        mock_proxy.get_account_storage.return_value = mock_standard_storage

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=100, request_delay=0
        )

        mock_proxy.get_account_storage.assert_called_once_with(test_address)
        assert result == mock_standard_storage

    def test_unexpected_error_logs_warning(self, mock_proxy, test_address, mock_config):
        """Test that unexpected errors are logged as warnings before fallback."""
        mock_proxy.do_post_generic.side_effect = KeyError("unexpected")

        mock_standard_storage = AccountStorage(raw={"pairs": {}}, entries=[])
        mock_proxy.get_account_storage.return_value = mock_standard_storage

        with patch("mxops.common.providers.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = get_account_storage_with_fallback(
                mock_proxy, test_address, num_keys=100, request_delay=0
            )

            # Verify warning was logged for unexpected error
            mock_logger.warning.assert_called()
            log_message = mock_logger.warning.call_args[0][0]
            assert "Unexpected error" in log_message
            assert "KeyError" in log_message

        mock_proxy.get_account_storage.assert_called_once()
        assert result == mock_standard_storage
