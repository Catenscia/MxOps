"""Tests for the providers module, specifically the dynamic batch sizing."""

from unittest.mock import MagicMock, patch

import pytest
from multiversx_sdk import AccountStorage, AccountStorageEntry, Address
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout

from mxops.common.providers import (
    _is_retryable_error,
    get_account_storage_with_fallback,
    set_state_with_batching,
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


class TestSetStateWithBatching:
    """Tests for the set_state_with_batching function."""

    @pytest.fixture
    def mock_proxy(self):
        """Create a mock proxy network provider."""
        return MagicMock()

    @pytest.fixture
    def mock_config(self):
        """Mock the Config.get_config() to return test values."""
        with patch("mxops.common.providers.Config") as mock:
            config_instance = MagicMock()
            config_instance.get.side_effect = lambda key: {
                "STORAGE_ITERATION_BATCH_SIZE": "100",
                "API_RATE_LIMIT": "100",
            }.get(key)
            mock.get_config.return_value = config_instance
            yield mock

    def test_small_storage_no_batching(self, mock_proxy, mock_config):
        """Test that small storage is sent in a single request."""
        account_state = {
            "address": "erd1abc...",
            "nonce": 5,
            "balance": "1000000000000000000",
            "pairs": {
                "6b657931": "76616c756531",
                "6b657932": "76616c756532",
            },
        }

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True, request_delay=0
        )

        mock_proxy.set_state_overwrite.assert_called_once_with([account_state])
        mock_proxy.set_state.assert_not_called()

    def test_small_storage_no_batching_no_overwrite(self, mock_proxy, mock_config):
        """Test that small storage uses set_state when overwrite=False."""
        account_state = {
            "address": "erd1abc...",
            "nonce": 5,
            "balance": "1000000000000000000",
            "pairs": {
                "6b657931": "76616c756531",
            },
        }

        set_state_with_batching(
            mock_proxy, account_state, overwrite=False, request_delay=0
        )

        mock_proxy.set_state.assert_called_once_with([account_state])
        mock_proxy.set_state_overwrite.assert_not_called()

    def test_large_storage_is_batched(self, mock_proxy, mock_config):
        """Test that large storage is split into batches."""
        # Create 250 pairs (should be split into 3 batches with batch_size=100)
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(250)}
        account_state = {
            "address": "erd1abc...",
            "nonce": 5,
            "balance": "1000000000000000000",
            "code": "0061736d",
            "pairs": pairs,
        }

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, request_delay=0
        )

        # First call should use set_state_overwrite with full metadata
        # Subsequent calls should use set_state with just address and pairs
        assert mock_proxy.set_state_overwrite.call_count == 1
        assert mock_proxy.set_state.call_count == 2

        # Verify first call has full metadata
        first_call_state = mock_proxy.set_state_overwrite.call_args[0][0][0]
        assert first_call_state["nonce"] == 5
        assert first_call_state["balance"] == "1000000000000000000"
        assert first_call_state["code"] == "0061736d"
        assert len(first_call_state["pairs"]) == 100

        # Verify subsequent calls only have address and pairs
        for call in mock_proxy.set_state.call_args_list:
            state = call[0][0][0]
            assert "address" in state
            assert "pairs" in state
            # Should not have full metadata in subsequent calls
            assert "nonce" not in state
            assert "balance" not in state
            assert "code" not in state

    def test_batch_reduction_on_timeout(self, mock_proxy, mock_config):
        """Test that batch size is reduced when timeout occurs."""
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(150)}
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        call_count = 0
        batch_sizes_observed = []

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            batch_sizes_observed.append(len(states[0]["pairs"]))
            if call_count == 1:
                raise Timeout("Connection timed out")
            # Success on subsequent calls

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=25, request_delay=0
        )

        # First call fails with 100, retry with 50, then continue
        assert batch_sizes_observed[0] == 100  # First attempt
        assert batch_sizes_observed[1] == 50   # Reduced batch

    def test_multiple_batch_reductions(self, mock_proxy, mock_config):
        """Test multiple batch size reductions before success."""
        # Need more than 100 pairs to trigger batching
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(150)}
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        call_count = 0
        batch_sizes_observed = []

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            batch_sizes_observed.append(len(states[0]["pairs"]))
            if call_count < 3:
                raise Timeout("Connection timed out")

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        # 100 -> 50 (timeout) -> 25 (success)
        assert batch_sizes_observed[0] == 100  # First batch
        assert batch_sizes_observed[1] == 50   # Reduced
        assert batch_sizes_observed[2] == 25   # Reduced again

    def test_raises_when_min_batch_exceeded(self, mock_proxy, mock_config):
        """Test that RuntimeError is raised when min batch size is exceeded."""
        # Need more than batch_size pairs to trigger batching
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(150)}
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        # Always timeout
        mock_proxy.set_state_overwrite.side_effect = Timeout("Always timeout")

        with pytest.raises(RuntimeError) as exc_info:
            set_state_with_batching(
                mock_proxy, account_state, overwrite=True,
                batch_size=100, min_batch_size=50, request_delay=0
            )

        assert "batch size reduced below minimum" in str(exc_info.value)
        assert "50" in str(exc_info.value)

    def test_non_retryable_error_raises_immediately(self, mock_proxy, mock_config):
        """Test that non-retryable errors are raised immediately."""
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(150)}
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        mock_proxy.set_state_overwrite.side_effect = ValueError("Invalid state")

        with pytest.raises(ValueError) as exc_info:
            set_state_with_batching(
                mock_proxy, account_state, overwrite=True,
                batch_size=100, request_delay=0
            )

        assert "Invalid state" in str(exc_info.value)
        # Should only be called once (no retry)
        assert mock_proxy.set_state_overwrite.call_count == 1

    def test_connection_error_triggers_batch_reduction(self, mock_proxy, mock_config):
        """Test that ConnectionError triggers batch size reduction."""
        # Need more than batch_size pairs to trigger batching
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(150)}
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        call_count = 0

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RequestsConnectionError("Connection refused")

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        assert call_count == 2  # First fails, second succeeds

    def test_http_502_triggers_batch_reduction(self, mock_proxy, mock_config):
        """Test that HTTP 502 errors trigger batch size reduction."""
        # Need more than batch_size pairs to trigger batching
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(150)}
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        call_count = 0

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_response = MagicMock()
                mock_response.status_code = 502
                raise HTTPError(response=mock_response)

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        assert call_count == 2

    def test_empty_pairs_sends_single_request(self, mock_proxy, mock_config):
        """Test that account state with empty pairs is sent in a single request."""
        account_state = {
            "address": "erd1abc...",
            "nonce": 5,
            "balance": "1000000000000000000",
            "pairs": {},
        }

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True, request_delay=0
        )

        mock_proxy.set_state_overwrite.assert_called_once_with([account_state])

    def test_no_pairs_key_sends_single_request(self, mock_proxy, mock_config):
        """Test that account state without pairs key is sent in a single request."""
        account_state = {
            "address": "erd1abc...",
            "nonce": 5,
            "balance": "1000000000000000000",
        }

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True, request_delay=0
        )

        mock_proxy.set_state_overwrite.assert_called_once_with([account_state])

    def test_logging_on_batch_reduction(self, mock_proxy, mock_config):
        """Test that batch reduction is logged."""
        # Need more than batch_size pairs to trigger batching
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(150)}
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        call_count = 0

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Timeout("Connection timed out")

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite

        with patch("mxops.common.providers.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            set_state_with_batching(
                mock_proxy, account_state, overwrite=True,
                batch_size=100, min_batch_size=10, request_delay=0
            )

            # Verify logger.info was called with batch reduction message
            mock_logger.info.assert_called()
            log_message = mock_logger.info.call_args_list[0][0][0]
            assert "failed with batch size" in log_message
            assert "reducing to" in log_message

    def test_progress_preserved_after_partial_success(self, mock_proxy, mock_config):
        """Test that successfully sent batches are not resent after a later failure.

        When batch 1 succeeds and batch 2 fails, only batch 2 should be retried.
        The pairs from batch 1 should not be resent.
        """
        # Create 200 pairs (will be 2 batches of 100)
        pairs = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                 for i in range(200)}
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        call_count = 0
        pairs_in_each_call = []

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            pairs_in_each_call.append(list(states[0]["pairs"].keys()))
            # First batch succeeds

        def mock_set_state(states):
            nonlocal call_count
            call_count += 1
            batch_pairs = list(states[0]["pairs"].keys())
            pairs_in_each_call.append(batch_pairs)
            # Fail on first set_state call (second batch)
            if call_count == 2:
                raise Timeout("Connection timed out")
            # Subsequent calls succeed

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite
        mock_proxy.set_state.side_effect = mock_set_state

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=25, request_delay=0
        )

        # Batch 1 (via set_state_overwrite): 100 pairs - succeeds
        # Batch 2 (via set_state): 100 pairs - fails (timeout)
        # Batch 2 retry (via set_state): 50 pairs - succeeds
        # Batch 2 part 2 (via set_state): 50 pairs - succeeds

        # Check that first batch pairs are not in any subsequent batches
        first_batch_pairs = set(pairs_in_each_call[0])
        for subsequent_batch in pairs_in_each_call[1:]:
            assert first_batch_pairs.isdisjoint(set(subsequent_batch)), \
                "Pairs from successful first batch should not be resent"

        # Verify all 200 pairs were sent exactly once (no duplicates, none missing)
        all_pairs_sent = []
        for batch in pairs_in_each_call:
            all_pairs_sent.extend(batch)
        # Check total count (may include retried pairs from failed batch)
        # But unique pairs should be exactly 200
        all_unique_pairs = set(all_pairs_sent)
        assert len(all_unique_pairs) == 200, \
            f"Expected 200 unique pairs, got {len(all_unique_pairs)}"

    def test_raises_on_invalid_min_batch_size(self, mock_proxy, mock_config):
        """Test that ValueError is raised when min_batch_size < 1."""
        account_state = {
            "address": "erd1abc...",
            "pairs": {"key": "value"},
        }

        with pytest.raises(ValueError) as exc_info:
            set_state_with_batching(
                mock_proxy, account_state, overwrite=True,
                min_batch_size=0, request_delay=0
            )

        assert "min_batch_size must be at least 1" in str(exc_info.value)

    def test_raises_on_missing_address(self, mock_proxy, mock_config):
        """Test that ValueError is raised when address is missing from account_state."""
        account_state = {
            "pairs": {"key": "value"},
        }

        with pytest.raises(ValueError) as exc_info:
            set_state_with_batching(
                mock_proxy, account_state, overwrite=True, request_delay=0
            )

        assert "account_state must contain 'address' key" in str(exc_info.value)


class TestGetAccountStorageWithFallbackBatchIncrease:
    """Tests for dynamic batch size increase in get_account_storage_with_fallback."""

    @pytest.fixture
    def mock_proxy(self):
        return MagicMock()

    @pytest.fixture
    def test_address(self):
        return Address.new_from_bech32(
            "erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"
        )

    @pytest.fixture
    def mock_config(self):
        with patch("mxops.common.providers.Config") as mock:
            config_instance = MagicMock()
            config_instance.get.side_effect = lambda key: {
                "STORAGE_ITERATION_BATCH_SIZE": "1000",
                "API_RATE_LIMIT": "100",
            }.get(key)
            mock.get_config.return_value = config_instance
            yield mock

    def test_batch_increase_on_smaller_payload(
        self, mock_proxy, test_address, mock_config
    ):
        """After timeout and reduction, smaller avg bytes/key triggers doubling."""
        call_count = 0

        # Large keys (20 bytes each) cause timeout, then small keys (4 bytes)
        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: large payload succeeds
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"aa" * 10: "bb" * 10},  # 40 bytes total, 1 key
                    "newIteratorState": [[1]],
                }
                return mock_resp
            elif call_count == 2:
                # Second call: timeout
                raise Timeout("Timeout")
            elif call_count == 3:
                # Third call: small payload succeeds (avg bytes/key < reference)
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"ab": "cd"},  # 4 bytes total, 1 key
                    "newIteratorState": [[2]],
                }
                return mock_resp
            else:
                # Fourth call: should use increased batch size, finish
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"ef": "01"},
                    "newIteratorState": [],
                }
                return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        result = get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        assert isinstance(result, AccountStorage)
        # Call 1: numKeys=200 (success)
        # Call 2: numKeys=200 (timeout) -> reduce to 100
        # Call 3: numKeys=100 (success, small payload -> increase to 200)
        # Call 4: numKeys=200 (success, done)
        assert mock_proxy.do_post_generic.call_args_list[0][0][1]["numKeys"] == 200
        assert mock_proxy.do_post_generic.call_args_list[1][0][1]["numKeys"] == 200
        assert mock_proxy.do_post_generic.call_args_list[2][0][1]["numKeys"] == 100
        assert mock_proxy.do_post_generic.call_args_list[3][0][1]["numKeys"] == 200

    def test_no_increase_when_payload_same_or_larger(
        self, mock_proxy, test_address, mock_config
    ):
        """No increase when avg bytes/key >= failure reference."""
        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Success with large keys (reference = 40 bytes/key)
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"aa" * 10: "bb" * 10},
                    "newIteratorState": [[1]],
                }
                return mock_resp
            elif call_count == 2:
                raise Timeout("Timeout")
            elif call_count == 3:
                # Success but payload still large (>= reference)
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"cc" * 10: "dd" * 10},  # Same 40 bytes/key
                    "newIteratorState": [],
                }
                return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        # Call 3 should still use reduced batch (no increase)
        assert mock_proxy.do_post_generic.call_args_list[2][0][1]["numKeys"] == 100

    def test_no_increase_when_first_request_times_out(
        self, mock_proxy, test_address, mock_config
    ):
        """No prior success means no increase after subsequent success."""
        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Timeout("Timeout")
            else:
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"ab": "cd"},
                    "newIteratorState": [],
                }
                return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        # Call 2 should use reduced batch (no increase, no reference)
        assert mock_proxy.do_post_generic.call_args_list[1][0][1]["numKeys"] == 100

    def test_recovery_reset_on_re_failure(
        self, mock_proxy, test_address, mock_config
    ):
        """After increase, another failure reduces and resets recovery."""
        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Success with large keys (reference)
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"aa" * 10: "bb" * 10},  # 40 bytes/key
                    "newIteratorState": [[1]],
                }
                return mock_resp
            elif call_count == 2:
                raise Timeout("First timeout")
            elif call_count == 3:
                # Small payload -> triggers increase back to 200
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"ab": "cd"},  # 4 bytes/key
                    "newIteratorState": [[2]],
                }
                return mock_resp
            elif call_count == 4:
                # Increased to 200 -> timeout again
                raise Timeout("Second timeout")
            else:
                # Reduced back to 100 -> success
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"ef": "01"},
                    "newIteratorState": [],
                }
                return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        # Call 4 at 200 (re-increased), call 5 at 100 (reduced again)
        assert mock_proxy.do_post_generic.call_args_list[3][0][1]["numKeys"] == 200
        assert mock_proxy.do_post_generic.call_args_list[4][0][1]["numKeys"] == 100

    def test_increase_capped_at_original(
        self, mock_proxy, test_address, mock_config
    ):
        """Doubling never exceeds original num_keys."""
        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Success (reference = 40 bytes/key)
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"aa" * 10: "bb" * 10},
                    "newIteratorState": [[1]],
                }
                return mock_resp
            elif call_count == 2:
                raise Timeout("Timeout")
            elif call_count <= 5:
                # Multiple successes with tiny payloads -> increase each time
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {f"0{call_count}": "0a"},
                    "newIteratorState": [[call_count]],
                }
                return mock_resp
            else:
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"0f": "0e"},
                    "newIteratorState": [],
                }
                return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        get_account_storage_with_fallback(
            mock_proxy, test_address, num_keys=200, request_delay=0, min_batch_size=50
        )

        batch_sizes = [
            call[0][1]["numKeys"]
            for call in mock_proxy.do_post_generic.call_args_list
        ]
        # After reduction to 100, increases: 200, 200 (capped), 200 (capped)
        assert all(s <= 200 for s in batch_sizes)

    def test_logging_on_batch_increase(
        self, mock_proxy, test_address, mock_config
    ):
        """INFO log emitted on batch increase with old/new sizes."""
        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"aa" * 10: "bb" * 10},
                    "newIteratorState": [[1]],
                }
                return mock_resp
            elif call_count == 2:
                raise Timeout("Timeout")
            else:
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"ab": "cd"},
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

            info_calls = [
                call[0][0] for call in mock_logger.info.call_args_list
            ]
            increase_logs = [m for m in info_calls if "increasing batch size" in m]
            assert len(increase_logs) == 1
            assert "from 100 to 200" in increase_logs[0]


class TestSetStateWithBatchingBatchIncrease:
    """Tests for dynamic batch size increase in set_state_with_batching."""

    @pytest.fixture
    def mock_proxy(self):
        return MagicMock()

    @pytest.fixture
    def mock_config(self):
        with patch("mxops.common.providers.Config") as mock:
            config_instance = MagicMock()
            config_instance.get.side_effect = lambda key: {
                "STORAGE_ITERATION_BATCH_SIZE": "100",
                "API_RATE_LIMIT": "100",
            }.get(key)
            mock.get_config.return_value = config_instance
            yield mock

    def test_batch_increase_on_smaller_avg_bytes_per_pair(
        self, mock_proxy, mock_config
    ):
        """After timeout, smaller avg bytes/pair triggers batch size doubling."""
        # First 100 pairs: large values (20 hex chars each)
        # Next 100 pairs: small values (2 hex chars each)
        large_pairs = {
            f"{'aa' * 10}{i:04x}": "bb" * 10 for i in range(100)
        }
        small_pairs = {
            f"cc{i:04x}": "dd" for i in range(100)
        }
        all_pairs = {**large_pairs, **small_pairs}
        account_state = {
            "address": "erd1abc...",
            "pairs": all_pairs,
        }

        call_count = 0
        batch_sizes = []

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            batch_sizes.append(len(states[0]["pairs"]))
            if call_count == 1:
                raise Timeout("Timeout")

        def mock_set_state(states):
            nonlocal call_count
            call_count += 1
            batch_sizes.append(len(states[0]["pairs"]))

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite
        mock_proxy.set_state.side_effect = mock_set_state

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        # Call 1: 100 large pairs -> timeout, reduce to 50
        # Subsequent calls: 50 pairs each, some will have small avg bytes
        # and trigger increase
        assert batch_sizes[0] == 100  # First attempt (fails)
        assert batch_sizes[1] == 50   # Reduced

    def test_no_increase_when_avg_bytes_same(self, mock_proxy, mock_config):
        """No increase when avg bytes/pair >= failure reference."""
        # All pairs same size -> avg never decreases
        pairs = {
            f"{'aa' * 5}{i:04x}": "bb" * 5 for i in range(200)
        }
        account_state = {
            "address": "erd1abc...",
            "pairs": pairs,
        }

        call_count = 0
        batch_sizes = []

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            batch_sizes.append(len(states[0]["pairs"]))
            if call_count == 1:
                raise Timeout("Timeout")

        def mock_set_state(states):
            nonlocal call_count
            call_count += 1
            batch_sizes.append(len(states[0]["pairs"]))

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite
        mock_proxy.set_state.side_effect = mock_set_state

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        # All batches after reduction should stay at 50 (no increase)
        for size in batch_sizes[1:]:
            assert size == 50

    def test_push_recovery_reset_on_re_failure(self, mock_proxy, mock_config):
        """After increase, re-failure reduces and resets recovery state."""
        # First 100: large pairs, next 100: small, next 100: large again
        large_pairs_1 = {f"{'aa' * 10}{i:04x}": "bb" * 10 for i in range(100)}
        small_pairs = {f"cc{i:04x}": "dd" for i in range(100)}
        large_pairs_2 = {f"{'ee' * 10}{i:04x}": "ff" * 10 for i in range(100)}
        all_pairs = {**large_pairs_1, **small_pairs, **large_pairs_2}
        account_state = {
            "address": "erd1abc...",
            "pairs": all_pairs,
        }

        call_count = 0
        batch_sizes = []

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            batch_sizes.append(len(states[0]["pairs"]))
            if call_count == 1:
                raise Timeout("First timeout")

        set_state_fail_on = set()

        def mock_set_state(states):
            nonlocal call_count
            call_count += 1
            batch_sizes.append(len(states[0]["pairs"]))
            if call_count in set_state_fail_on:
                raise Timeout("Re-failure")

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite
        mock_proxy.set_state.side_effect = mock_set_state

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        # Verify: first batch fails at 100, reduces to 50
        assert batch_sizes[0] == 100
        assert batch_sizes[1] == 50

    def test_push_increase_capped_at_original(self, mock_proxy, mock_config):
        """Batch size increase never exceeds original batch_size."""
        # Large pairs then very small pairs
        large_pairs = {f"{'aa' * 10}{i:04x}": "bb" * 10 for i in range(100)}
        small_pairs = {f"c{i:02x}": "d" for i in range(400)}
        all_pairs = {**large_pairs, **small_pairs}
        account_state = {
            "address": "erd1abc...",
            "pairs": all_pairs,
        }

        call_count = 0
        batch_sizes = []

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            batch_sizes.append(len(states[0]["pairs"]))
            if call_count == 1:
                raise Timeout("Timeout")

        def mock_set_state(states):
            nonlocal call_count
            call_count += 1
            batch_sizes.append(len(states[0]["pairs"]))

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite
        mock_proxy.set_state.side_effect = mock_set_state

        set_state_with_batching(
            mock_proxy, account_state, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        # No batch should exceed original batch_size of 100
        for size in batch_sizes:
            assert size <= 100

    def test_push_logging_on_batch_increase(self, mock_proxy, mock_config):
        """INFO log emitted when batch size increases on push."""
        # Large pairs then small pairs
        large_pairs = {f"{'aa' * 10}{i:04x}": "bb" * 10 for i in range(100)}
        small_pairs = {f"c{i:02x}": "d" for i in range(200)}
        all_pairs = {**large_pairs, **small_pairs}
        account_state = {
            "address": "erd1abc...",
            "pairs": all_pairs,
        }

        call_count = 0

        def mock_set_state_overwrite(states):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Timeout("Timeout")

        def mock_set_state(states):
            nonlocal call_count
            call_count += 1

        mock_proxy.set_state_overwrite.side_effect = mock_set_state_overwrite
        mock_proxy.set_state.side_effect = mock_set_state

        with patch("mxops.common.providers.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            set_state_with_batching(
                mock_proxy, account_state, overwrite=True,
                batch_size=100, min_batch_size=10, request_delay=0
            )

            info_calls = [
                call[0][0] for call in mock_logger.info.call_args_list
            ]
            increase_logs = [m for m in info_calls if "increasing" in m]
            assert len(increase_logs) >= 1
            assert "avg bytes/pair" in increase_logs[0]


class TestBatchSizeResetBetweenAccounts:
    """Verify batch size is reset between accounts (existing behavior)."""

    @pytest.fixture
    def mock_proxy(self):
        return MagicMock()

    @pytest.fixture
    def mock_config(self):
        with patch("mxops.common.providers.Config") as mock:
            config_instance = MagicMock()
            config_instance.get.side_effect = lambda key: {
                "STORAGE_ITERATION_BATCH_SIZE": "1000",
                "API_RATE_LIMIT": "100",
            }.get(key)
            mock.get_config.return_value = config_instance
            yield mock

    def test_fetch_batch_size_reset_between_accounts(self, mock_proxy, mock_config):
        """Two sequential fetch calls each start at default batch size."""
        address_a = Address.new_from_bech32(
            "erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"
        )
        address_b = Address.new_from_bech32(
            "erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"
        )

        call_count = 0
        batch_sizes_per_call = []

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            batch_sizes_per_call.append(data["numKeys"])

            if call_count == 1:
                # Account A: first call timeout -> reduce
                raise Timeout("Timeout")
            else:
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"ab": "cd"},
                    "newIteratorState": [],
                }
                return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        # Account A: starts at 200, reduces to 100
        get_account_storage_with_fallback(
            mock_proxy, address_a, num_keys=200, request_delay=0, min_batch_size=50
        )

        # Account B: should start fresh at 200
        get_account_storage_with_fallback(
            mock_proxy, address_b, num_keys=200, request_delay=0, min_batch_size=50
        )

        # Account A: 200 (fail), 100 (success)
        # Account B: 200 (success) - reset to original
        assert batch_sizes_per_call[0] == 200  # A first attempt
        assert batch_sizes_per_call[1] == 100  # A reduced
        assert batch_sizes_per_call[2] == 200  # B starts fresh

    def test_push_batch_size_reset_between_accounts(self, mock_proxy, mock_config):
        """Two sequential push calls each start at default batch size."""
        pairs_a = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                   for i in range(150)}
        state_a = {"address": "erd1aaa...", "pairs": pairs_a}

        pairs_b = {f"key{i:04d}".encode().hex(): f"val{i}".encode().hex()
                   for i in range(150, 300)}
        state_b = {"address": "erd1bbb...", "pairs": pairs_b}

        call_count_a = 0
        batch_sizes_a = []
        batch_sizes_b = []

        def mock_overwrite_a(states):
            nonlocal call_count_a
            call_count_a += 1
            batch_sizes_a.append(len(states[0]["pairs"]))
            if call_count_a == 1:
                raise Timeout("Timeout")

        mock_proxy.set_state_overwrite.side_effect = mock_overwrite_a

        # Account A: batch 100 -> timeout -> reduce to 50
        set_state_with_batching(
            mock_proxy, state_a, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        def mock_overwrite_b(states):
            batch_sizes_b.append(len(states[0]["pairs"]))

        mock_proxy.set_state_overwrite.side_effect = mock_overwrite_b
        mock_proxy.set_state.side_effect = lambda s: batch_sizes_b.append(
            len(s[0]["pairs"])
        )

        # Account B: should start fresh at 100
        set_state_with_batching(
            mock_proxy, state_b, overwrite=True,
            batch_size=100, min_batch_size=10, request_delay=0
        )

        assert batch_sizes_a[0] == 100  # A first attempt (fails)
        assert batch_sizes_a[1] == 50   # A reduced
        assert batch_sizes_b[0] == 100  # B starts fresh

    def test_fetch_fallback_does_not_affect_next_account(
        self, mock_proxy, mock_config
    ):
        """Account A falling back to standard doesn't affect account B."""
        address_a = Address.new_from_bech32(
            "erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"
        )
        address_b = Address.new_from_bech32(
            "erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"
        )

        call_count = 0

        def side_effect(url, data):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # Account A: all calls timeout -> fallback
                raise Timeout("Always timeout")
            else:
                # Account B: succeeds
                mock_resp = MagicMock()
                mock_resp.to_dictionary.return_value = {
                    "pairs": {"ab": "cd"},
                    "newIteratorState": [],
                }
                return mock_resp

        mock_proxy.do_post_generic.side_effect = side_effect

        mock_standard = AccountStorage(raw={"pairs": {}}, entries=[])
        mock_proxy.get_account_storage.return_value = mock_standard

        # Account A: exhausts min_batch, falls back
        get_account_storage_with_fallback(
            mock_proxy, address_a, num_keys=100, request_delay=0, min_batch_size=50
        )
        mock_proxy.get_account_storage.assert_called_once()

        # Account B: starts fresh at 200, succeeds via paginated
        result = get_account_storage_with_fallback(
            mock_proxy, address_b, num_keys=200, request_delay=0, min_batch_size=50
        )

        assert isinstance(result, AccountStorage)
        assert len(result.entries) == 1
        # Account B used the full 200, not any reduced value
        assert mock_proxy.do_post_generic.call_args_list[-1][0][1]["numKeys"] == 200
